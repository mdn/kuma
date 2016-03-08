from django.http import HttpResponseRedirect
from django.shortcuts import render

from kuma.core.utils import urlparams

from .exceptions import ReadOnlyException
from .jobs import DocumentZoneURLRemapsJob


class ReadOnlyMiddleware(object):
    """
    Renders a 403.html page with a flag for a specific message.
    """
    def process_exception(self, request, exception):
        if isinstance(exception, ReadOnlyException):
            context = {'reason': exception.args[0]}
            return render(request, '403.html', context, status=403)
        return None


class DocumentZoneMiddleware(object):
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

        remaps = DocumentZoneURLRemapsJob().get(request.LANGUAGE_CODE)
        for original_path, new_path in remaps:

            if (
                request.path_info == original_path or
                request.path_info.startswith(u''.join([original_path, '/']))
            ):
                # Is this a request for the "original" wiki path? Redirect to
                # new URL root, if so.
                new_path = request.path_info.replace(original_path,
                                                     new_path,
                                                     1)
                new_path = '/%s%s' % (request.LANGUAGE_CODE, new_path)

                query = request.GET.copy()
                if 'lang' in query:
                    query.pop('lang')
                new_path = urlparams(new_path, query_dict=query)

                return HttpResponseRedirect(new_path)

            elif request.path_info.startswith(new_path):
                # Is this a request for the relocated wiki path? If so, rewrite
                # the path as a request for the proper wiki view.
                request.path_info = request.path_info.replace(new_path,
                                                              original_path,
                                                              1)
                break
