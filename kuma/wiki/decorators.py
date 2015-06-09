try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

import newrelic.agent
from waffle import flag_is_active, switch_is_active

from django.http import HttpResponsePermanentRedirect, Http404
from jingo.helpers import urlparams

from kuma.core.urlresolvers import reverse

from .exceptions import ReadOnlyException
from .utils import locale_and_slug_from_path


def prevent_indexing(func):
    """Decorator to prevent a page from being indexable by robots"""
    @wraps(func)
    def _added_header(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        response['X-Robots-Tag'] = 'noindex'
        return response
    return _added_header


def allow_CORS_GET(func):
    """Decorator to allow CORS for GET requests"""
    @wraps(func)
    def _added_header(request, *args, **kwargs):
        response = func(request, *args, **kwargs)

        # We are using this switch temporarily to research bug 1104260.
        # Disabling this code has no effect locally, but may have an effect on
        # production.
        if 'GET' == request.method and switch_is_active('application_ACAO'):
            response['Access-Control-Allow-Origin'] = "*"
        return response
    return _added_header


def check_readonly(view):
    """Decorator to enable readonly mode"""
    def _check_readonly(request, *args, **kwargs):
        if not flag_is_active(request, 'kumaediting'):
            raise ReadOnlyException("kumaediting")
        elif flag_is_active(request, 'kumabanned'):
            raise ReadOnlyException("kumabanned")

        return view(request, *args, **kwargs)
    return _check_readonly


@newrelic.agent.function_trace()
def process_document_path(func, reverse_name='wiki.document'):
    """
    Decorator to process document_path into locale and slug, with
    auto-redirect if necessary.

    This function takes generic args and kwargs so it can presume as little
    as possible on the view method signature.
    """
    @wraps(func)
    def process(request, document_path=None, *args, **kwargs):

        if kwargs.get('bypass_process_document_path', False):
            # Support an option to bypass this decorator altogether, so one
            # view can directly call another view.
            del kwargs['bypass_process_document_path']
            return func(request, document_path, *args, **kwargs)

        document_slug, document_locale = None, None
        if document_path:

            # Parse the document path into locale and slug.
            document_locale, document_slug, needs_redirect = (
                locale_and_slug_from_path(document_path, request))

            # Add check for "local" URL, remove trailing slash
            slug_length = len(document_slug)
            if slug_length and document_slug[slug_length - 1] == '/':
                needs_redirect = True
                document_slug = document_slug.rstrip('/')

            if not document_slug:
                # If there's no slug, then this is just a 404.
                raise Http404

            if request.GET.get('raw', False) is not False:
                # HACK: There are and will be a lot of kumascript templates
                # based on legacy DekiScript which will attempt to request
                # old-style URLs. Skip 301 redirects for raw content.
                needs_redirect = False

            if needs_redirect:
                # This catches old MindTouch locales, missing locale, and a few
                # other cases to fire off a 301 Moved permanent redirect.
                url = reverse('wiki.document', locale=document_locale,
                              args=[document_slug])
                url = urlparams(url, query_dict=request.GET)
                return HttpResponsePermanentRedirect(url)

        # Set the kwargs that decorated methods will expect.
        kwargs['document_slug'] = document_slug
        kwargs['document_locale'] = document_locale
        return func(request, *args, **kwargs)

    return process
