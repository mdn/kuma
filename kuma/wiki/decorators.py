from functools import wraps

import newrelic.agent
from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect

from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams


def allow_CORS_GET(func):
    """Decorator to allow CORS for GET requests"""

    @wraps(func)
    def _added_header(request, *args, **kwargs):
        response = func(request, *args, **kwargs)

        if "GET" == request.method:
            response["Access-Control-Allow-Origin"] = "*"
        return response

    return _added_header


@newrelic.agent.function_trace()
def process_document_path(func, reverse_name="wiki.document"):
    """
    Decorator to process document_path into locale and slug, with
    auto-redirect if necessary.

    This function takes generic args and kwargs so it can presume as little
    as possible on the view method signature.
    """

    @wraps(func)
    def process(request, document_path=None, *args, **kwargs):

        if kwargs.get("bypass_process_document_path", False):
            # Support an option to bypass this decorator altogether, so one
            # view can directly call another view.
            del kwargs["bypass_process_document_path"]
            return func(request, document_path, *args, **kwargs)

        document_slug, document_locale = None, None
        if document_path:

            # Parse the document path into locale and slug.
            document_locale, document_slug, needs_redirect = locale_and_slug_from_path(
                document_path, request
            )

            # Add check for "local" URL, remove trailing slash
            slug_length = len(document_slug)
            if slug_length and document_slug[slug_length - 1] == "/":
                needs_redirect = True
                document_slug = document_slug.rstrip("/")

            if not document_slug:
                # If there's no slug, then this is just a 404.
                raise Http404

            if request.GET.get("raw", False) is not False:
                # HACK: There are and will be a lot of kumascript templates
                # based on legacy DekiScript which will attempt to request
                # old-style URLs. Skip 301 redirects for raw content.
                # TODO: evaluate if this is still appropriate
                needs_redirect = False

            if needs_redirect:
                # This catches old MindTouch locales, missing locale, and a few
                # other cases to fire off a 301 Moved permanent redirect.
                url = reverse(
                    "wiki.document", locale=document_locale, args=[document_slug]
                )
                url = urlparams(url, query_dict=request.GET)
                return HttpResponsePermanentRedirect(url)

        # Set the kwargs that decorated methods will expect.
        kwargs["document_slug"] = document_slug
        kwargs["document_locale"] = document_locale
        return func(request, *args, **kwargs)

    return process


def locale_and_slug_from_path(path, request=None, path_locale=None):
    """Given a proposed doc path, try to see if there's a legacy MindTouch
    locale or even a modern Kuma domain in the path. If so, signal for a
    redirect to a more canonical path. In any case, produce a locale and
    slug derived from the given path."""
    locale, slug, needs_redirect = "", path, False
    mdn_locales = {lang[0].lower(): lang[0] for lang in settings.LANGUAGES}

    # If there's a slash in the path, then the first segment could be a
    # locale. And, that locale could even be a legacy MindTouch locale.
    if "/" in path:
        maybe_locale, maybe_slug = path.split("/", 1)
        l_locale = maybe_locale.lower()

        if l_locale in settings.MT_TO_KUMA_LOCALE_MAP:
            # The first segment looks like a MindTouch locale, remap it.
            needs_redirect = True
            locale = settings.MT_TO_KUMA_LOCALE_MAP[l_locale]
            slug = maybe_slug

        elif l_locale in mdn_locales:
            # The first segment looks like an MDN locale, redirect.
            needs_redirect = True
            locale = mdn_locales[l_locale]
            slug = maybe_slug

    # No locale yet? Try the locale detected by the request or in path
    if locale == "":
        if request:
            locale = request.LANGUAGE_CODE
        elif path_locale:
            locale = path_locale

    # Still no locale? Probably no request. Go with the site default.
    if locale == "":
        locale = getattr(settings, "WIKI_DEFAULT_LANGUAGE", "en-US")

    return (locale, slug, needs_redirect)
