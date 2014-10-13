import contextlib
import re
import urllib

from django.core import urlresolvers
from django.http import HttpResponsePermanentRedirect, HttpResponseForbidden
from django.utils.encoding import iri_to_uri, smart_str, smart_unicode

import tower

from devmo import get_mysql_error
from sumo.helpers import urlparams
from sumo.urlresolvers import Prefixer, set_url_prefixer, split_path
from sumo.views import handle403


# Django compatibility shim. Once we're on Django 1.4, do:
# from django.db.utils import DatabaseError
DatabaseError = get_mysql_error()


class LocaleURLMiddleware(object):
    """
    Based on zamboni.amo.middleware.
    Tried to use localeurl but it choked on 'en-US' with capital letters.

    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def process_request(self, request):
        prefixer = Prefixer(request)
        set_url_prefixer(prefixer)
        full_path = prefixer.fix(prefixer.shortened_path)

        if 'lang' in request.GET:
            # Blank out the locale so that we can set a new one. Remove lang
            # from the query params so we don't have an infinite loop.
            prefixer.locale = ''
            new_path = prefixer.fix(prefixer.shortened_path)
            query = dict((smart_str(k), v) for
                         k, v in request.GET.iteritems() if k != 'lang')
            return HttpResponsePermanentRedirect(urlparams(new_path, **query))

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponsePermanentRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, _ = split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.locale = prefixer.locale
        tower.activate(prefixer.locale)

    def process_response(self, request, response):
        """Unset the thread-local var we set during `process_request`."""
        # This makes mistaken tests (that should use LocalizingClient but
        # use Client instead) fail loudly and reliably. Otherwise, the set
        # prefixer bleeds from one test to the next, making tests
        # order-dependent and causing hard-to-track failures.
        set_url_prefixer(None)
        return response

    def process_exception(self, request, exception):
        set_url_prefixer(None)


class Forbidden403Middleware(object):
    """
    Renders a 403.html page if response.status_code == 403.
    """
    def process_response(self, request, response):
        if isinstance(response, HttpResponseForbidden):
            return handle403(request)
        # If not 403, return response unmodified
        return response


class NoCacheHttpsMiddleware(object):
    """
    Sets no-cache headers when HTTPS META variable is set
    and not equal to 'off'.
    """
    def process_response(self, request, response):
        if 'HTTPS' in request.META and request.META['HTTPS'] != 'off':
            response['Expires'] = 'Thu, 19 Nov 1981 08:52:00 GMT'
            response['Cache-Control'] = 'no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
        return response


class PlusToSpaceMiddleware(object):
    """Replace old-style + with %20 in URLs."""
    def process_request(self, request):
        p = re.compile(r'\+')
        if p.search(request.path_info):
            new = p.sub(' ', request.path_info)
            if request.META['QUERY_STRING']:
                new = u'%s?%s' % (new,
                                  smart_unicode(request.META['QUERY_STRING']))
            if hasattr(request, 'locale'):
                new = u'/%s%s' % (request.locale, new)
            return HttpResponsePermanentRedirect(new)


def is_valid_path(request, path):
    urlconf = getattr(request, 'urlconf', None)
    try:
        urlresolvers.resolve(path, urlconf)
        return True
    except urlresolvers.Resolver404:
        return False


class RemoveSlashMiddleware(object):
    """
    Middleware that tries to remove a trailing slash if there was a 404.

    If the response is a 404 because url resolution failed, we'll look for a
    better url without a trailing slash.
    """

    def process_response(self, request, response):
        if (response.status_code == 404
            and request.path_info.endswith('/')
            and not is_valid_path(request, request.path_info)
            and is_valid_path(request, request.path_info[:-1])):
            # Use request.path because we munged app/locale in path_info.
            newurl = request.path[:-1]
            if request.GET:
                with safe_query_string(request):
                    newurl += '?' + request.META['QUERY_STRING']
            return HttpResponsePermanentRedirect(newurl)
        return response


@contextlib.contextmanager
def safe_query_string(request):
    """
    Turn the QUERY_STRING into a unicode- and ascii-safe string.

    We need unicode so it can be combined with a reversed URL, but it has to be
    ascii to go in a Location header.  iri_to_uri seems like a good compromise.
    """
    qs = request.META['QUERY_STRING']
    try:
        request.META['QUERY_STRING'] = iri_to_uri(qs)
        yield
    finally:
        request.META['QUERY_STRING'] = qs
