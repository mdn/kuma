import logging

from django.shortcuts import render
from django.http import HttpResponsePermanentRedirect, HttpResponseForbidden
from django.utils.encoding import iri_to_uri, smart_str, smart_unicode

from sumo.helpers import urlparams
from sumo.urlresolvers import reverse

from wiki import ReadOnlyException
from wiki.models import (Document, DocumentZone)


class ReadOnlyMiddleware(object):
    """
    Renders a 403.html page with a flag for a specific message.
    """
    def process_exception(self, request, exception):
        if isinstance(exception, ReadOnlyException):
            return render(request, '403.html',
                                {'reason': exception.args[0]},
                                status=403)
        return None


class DocumentZoneMiddleware(object):
    """
    For document zones with specified URL roots, this middleware modifies the
    incoming path_info to point at the internal wiki path
    """
    def process_request(self, request):
        zones = DocumentZone.objects.filter(url_root__isnull=False)
        for z in zones:
            root = '/%s' % z.url_root
            orig_path = '/docs/%s' % (z.document.slug)

            if request.path_info.startswith(orig_path):
                
                new_path = request.path_info.replace(orig_path, root, 1)
                new_path = '/%s%s' % (request.locale, new_path)
                
                query = dict((smart_str(k), v) for
                             k, v in request.GET.iteritems() if k != 'lang')
                new_path = urlparams(new_path, **query)

                return HttpResponsePermanentRedirect(new_path)

            if request.path_info.startswith(root):
                request.path_info = request.path_info.replace(
                    root, '/docs/%s' % z.document.slug, 1)
                break
