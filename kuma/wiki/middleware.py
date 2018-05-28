from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
# TODO: Remove the try-except wrapper after move to Django 1.10+.
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
from django.views.decorators.cache import never_cache

from kuma.core.i18n import get_kuma_languages
from kuma.core.utils import urlparams

from .exceptions import ReadOnlyException
from .jobs import DocumentZoneURLRemapsJob


class ReadOnlyMiddleware(MiddlewareMixin):
    """
    Renders a 403.html page with a flag for a specific message.
    """
    def process_exception(self, request, exception):
        if isinstance(exception, ReadOnlyException):
            context = {'reason': exception.args[0]}
            return never_cache(render)(request, '403.html', context,
                                       status=403)
        return None


class DocumentZoneMiddleware(MiddlewareMixin):
    """
    For document zones with specified URL roots, this middleware modifies the
    incoming path_info to point at the internal wiki path
    """
    def process_request(self, request):
        # https://bugzil.la/1189222
        # Don't redirect POST $subscribe requests to GET zone url
        if (request.method == 'POST' and
                ('$subscribe' in request.path or '$files' in request.path)):
            return None

        # Skip slugs that don't have locales, and won't be in a zone
        path = request.path_info
        request_slug = path.lstrip('/')
        if any(request_slug.startswith(slug)
               for slug in settings.LANGUAGE_URL_IGNORED_PATHS):
            return None

        # Convert the request path to zamboni/amo style
        maybe_lang = request_slug.split(u'/')[0]
        if maybe_lang in get_kuma_languages():
            path = u'/' + u'/'.join(request_slug.split(u'/')[1:])
        else:
            path = u'/' + request_slug

        remaps = DocumentZoneURLRemapsJob().get(request.LANGUAGE_CODE)
        for original_path, new_path in remaps:

            if (
                path == original_path or
                path.startswith(u''.join([original_path, '/']))
            ):
                # Is this a request for the "original" wiki path? Redirect to
                # new URL root, if so.
                new_path = path.replace(original_path, new_path, 1)
                new_path = '/%s%s' % (request.LANGUAGE_CODE, new_path)

                query = request.GET.copy()
                new_path = urlparams(new_path, query_dict=query)

                return HttpResponseRedirect(new_path)

            elif path == u'/docs{}'.format(new_path):
                # Is this a request for a DocumentZone, but with /docs/ wedged
                # in the url path between the language code and the zone's url_root?
                new_path = u'/{}{}'.format(request.LANGUAGE_CODE, new_path)
                query = request.GET.copy()
                new_path = urlparams(new_path, query_dict=query)

                return HttpResponseRedirect(new_path)

            elif path.startswith(new_path):
                # Is this a request for the relocated wiki path? If so, rewrite
                # the path as a request for the proper wiki view.
                request.path_info = request.path_info.replace(new_path,
                                                              original_path,
                                                              1)
                break
