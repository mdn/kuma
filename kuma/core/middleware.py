from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import MiddlewareNotUsed
from django.http import (HttpResponseForbidden,
                         HttpResponsePermanentRedirect,
                         HttpResponseRedirect)
from django.urls import get_script_prefix, resolve, Resolver404
from django.utils.encoding import smart_str
from waffle.middleware import WaffleMiddleware

from kuma.wiki.views.legacy import (mindtouch_to_kuma_redirect,
                                    mindtouch_to_kuma_url)

from .decorators import add_shared_cache_control
from .i18n import (activate_language_from_request,
                   get_kuma_languages,
                   get_language,
                   get_language_from_path,
                   get_language_from_request)
from .utils import is_untrusted, urlparams
from .views import handler403


class MiddlewareBase(object):

    def __init__(self, get_response):
        self.get_response = get_response


class LangSelectorMiddleware(MiddlewareBase):
    """
    Redirect requests with a ?lang= parameter.

    This should appear higher than LocaleMiddleware in the middleware list.
    """

    def __call__(self, request):
        """Redirect if ?lang query parameter is valid."""
        query_lang = request.GET.get('lang')
        if not (query_lang and query_lang in get_kuma_languages()):
            # Invalid or no language requested, so don't redirect.
            return self.get_response(request)

        # Check if the requested language is already embedded in URL
        language = get_language_from_request(request)
        script_prefix = get_script_prefix()
        lang_prefix = f'{script_prefix}{language}/'
        full_path = request.get_full_path()  # Includes querystring
        old_path = urlsplit(full_path).path
        new_prefix = f'{script_prefix}{query_lang}/'
        if full_path.startswith(lang_prefix):
            new_path = old_path.replace(lang_prefix, new_prefix, 1)
        else:
            new_path = old_path.replace(script_prefix, new_prefix, 1)

        # Redirect to same path with requested language and without ?lang
        new_query = dict((smart_str(k), v) for
                         k, v in request.GET.items() if k != 'lang')
        if new_query:
            new_path = urlparams(new_path, **new_query)
        response = HttpResponseRedirect(new_path)
        add_shared_cache_control(response)
        return response


class LocaleStandardizerMiddleware(MiddlewareBase):
    """
    Convert 404s with legacy locales to redirects.

    This should appear higher than LocaleMiddleware in the middleware list.
    """

    def __call__(self, request):
        """Convert 404s into redirects to language-specific URLs."""

        response = self.get_response(request)

        if response.status_code != 404:
            return response

        # Get the language code picked based on the path
        language_from_path = get_language_from_path(request.path_info)
        if not language_from_path:
            # 404 URLs without locale prefixes should remain 404s
            return response

        literal_from_path = request.path_info.split('/')[1]
        fixed_locale = None
        lower_literal = literal_from_path.lower()
        lower_language = language_from_path.lower()
        match = literal_from_path == language_from_path
        lower_match = lower_literal == lower_language

        if not match and lower_match:
            # Convert locale prefix to the preferred case (en-us -> en-US)
            fixed_locale = language_from_path
        elif lower_literal in settings.LOCALE_ALIASES:
            # Fix special cases (cn -> zh-CN, zh-Hans -> zh-CN)
            fixed_locale = settings.LOCALE_ALIASES[lower_literal]
        elif not match and lower_literal.startswith(lower_language):
            # Convert regional to generic locale prefix (fr-FR -> fr)
            # Case-insensitive so FR-Fr also goes to fr
            fixed_locale = language_from_path
        elif not match and lower_language.startswith(lower_literal):
            # Convert generic to regional locale prefix (pt -> pt-PT)
            # Case-insensitive so PT -> pt-PT and En -> en-US
            fixed_locale = language_from_path

        if fixed_locale:
            # Replace the 404 with a redirect to the fixed locale
            full_path = request.get_full_path()
            fixed_path = full_path.replace(literal_from_path, fixed_locale, 1)
            redirect_response = HttpResponseRedirect(fixed_path)
            add_shared_cache_control(redirect_response)
            return redirect_response

        # No language fixup found, return the 404
        return response


class LocaleMiddleware(MiddlewareBase):
    """
    This is a very simple middleware that parses a request
    and decides what translation object to install in the current
    thread context. This allows pages to be dynamically
    translated to the language the user desires (if the language
    is available, of course).

    Based on Django 1.11.16's LocaleMiddleware from
    django/middleware/locale.py, with changes:

    * Use MiddlewareBase, don't support old-style middleware
    * Assume that locale prefixes, and no implied default locale, are in use
    * Use Kuma language codes (en-US) instead of Django's (en-us),
      via our get_language()
    * Use Kuma-prefered locales (zn-CN) instead of Django's (zn-Hans)
    * Don't include "Vary: Accept-Language" header
    * Add caching headers to locale redirects

    The process_request logic, modified for Kuma language codes, is in
    kuma.core.i18n.activate_language_from_request, so it can be called from
    kuma.search tests.
    """

    def __call__(self, request):
        """
        Execute the middleware.

        A more generic version is provided by MiddlewareMixin in Django.
        """
        # Activate the language, and add LANGUAGE_CODE to the request.
        # In Django, this is self.process_request()
        activate_language_from_request(request)

        response = self.get_response(request)
        response = self.process_response(request, response)
        return response

    def process_response(self, request, response):
        """Add Content-Language, convert some 404s to locale redirects."""
        language = get_language()
        language_from_path = get_language_from_path(request.path_info)
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)

        # Kuma: assume locale-prefix patterns, including default language
        if response.status_code == 404 and not language_from_path:
            # Maybe the language code is missing in the URL? Try adding the
            # language prefix and redirecting to that URL.
            language_path = f'/{language}{request.path_info}'
            path_valid = is_valid_path(language_path, language, urlconf)
            path_needs_slash = (
                not path_valid and (
                    settings.APPEND_SLASH and not language_path.endswith('/') and
                    is_valid_path('%s/' % language_path, language, urlconf)
                )
            )

            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                # Insert language after the script prefix and before the
                # rest of the URL
                language_url = (
                    request.get_full_path(force_append_slash=path_needs_slash)
                    .replace(
                        script_prefix,
                        f'{script_prefix}{language}/',
                        1
                    ))
                # Kuma: Add caching headers to redirect
                if request.path_info == '/':
                    # Only the homepage should be redirected permanently.
                    redirect = HttpResponsePermanentRedirect(language_url)
                else:
                    redirect = HttpResponseRedirect(language_url)
                add_shared_cache_control(redirect)
                return redirect

        # Kuma: Do not add 'Accept-Language' to Vary header
        # if not (i18n_patterns_used and language_from_path):
        #    patch_vary_headers(response, ('Accept-Language',))

        # Kuma: Add a pragma, since never skipped
        # No views set this header, so the middleware always sets it. The code
        # could be replaced with an assertion, but that would deviate from
        # Django's version, and make the code brittle, so using a pragma
        # instead. And a long comment.
        if 'Content-Language' not in response:  # pragma: no cover
            response['Content-Language'] = language

        return response


class Forbidden403Middleware(MiddlewareBase):
    """
    Renders a 403.html page if response.status_code == 403.
    """

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, HttpResponseForbidden):
            return handler403(request)
        # If not 403, return response unmodified
        return response


def is_valid_path(path, language_code, urlconf=None):
    """
    Return True if the given path resolves against the default URL resolver,
    False otherwise. This is a convenience method to make working with "is
    this a match?" cases easier, avoiding try...except blocks.

    Based on Django 1.11.16's is_valid_path from django.urls.is_valid_path,
    with changes:
    * If the catch-all mindtouch_to_kuma_redirect was the match, check if it
      would return a 404.
    * Adds a required language_code parameter, for mindtouch_to_kuma_url
    """
    try:
        match = resolve(path, urlconf)
        if match.func == mindtouch_to_kuma_redirect:
            # mindtouch_to_kuma_redirect matches everything.
            # Check if it would return a redirect or 404.
            url = mindtouch_to_kuma_url(language_code,
                                        match.kwargs['path'])
            return bool(url)
        else:
            return True
    except Resolver404:
        return False


class SlashMiddleware(MiddlewareBase):
    """
    Middleware that adds or removes a trailing slash if there was a 404.

    If the response is a 404 because URL resolution failed, we'll look for a
    better URL with or without a trailing slash.

    The LocaleMiddleware turns 404s to redirects if a locale prefix is needed.
    It will also add a trailing slash to make a valid URL.

    The CommonMiddleware is supposed to handle adding slashes to 404s, but
    doesn't work because the catch-all mindtouch_to_kuma_redirect function
    makes it so that Django's is_valid_url returns True for all URLs.
    """

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path_info
        language = getattr(request, 'LANGUAGE_CODE') or settings.LANGUAGE_CODE
        if response.status_code == 404 and not is_valid_path(path, language):
            new_path = None
            if path.endswith('/') and is_valid_path(path[:-1], language):
                # Remove the trailing slash for a valid URL
                new_path = path[:-1]
            elif not path.endswith('/') and is_valid_path(path + '/', language):
                # Add a trailing slash for a valid URL
                new_path = path + '/'
            if new_path:
                if request.GET:
                    new_path += '?' + request.META['QUERY_STRING']
                return HttpResponsePermanentRedirect(new_path)
        return response


class SetRemoteAddrFromForwardedFor(MiddlewareBase):
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1.
    """

    def __call__(self, request):
        try:
            forwarded_for = request.META['HTTP_X_FORWARDED_FOR']
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # The client's IP will be the first one.
            forwarded_for = forwarded_for.split(',')[0].strip()
            request.META['REMOTE_ADDR'] = forwarded_for

        return self.get_response(request)


class ForceAnonymousSessionMiddleware(SessionMiddleware):

    def process_request(self, request):
        """
        Always create an anonymous session.
        """
        request.session = self.SessionStore(None)

    def process_response(self, request, response):
        """
        Override the base-class method to ensure we do nothing.
        """
        return response


class RestrictedEndpointsMiddleware(MiddlewareBase):
    """Restricts the accessible endpoints based on the host."""

    def __init__(self, get_response):
        if not settings.ENABLE_RESTRICTIONS_BY_HOST:
            raise MiddlewareNotUsed
        super(RestrictedEndpointsMiddleware, self).__init__(get_response)

    def __call__(self, request):
        if is_untrusted(request):
            request.urlconf = 'kuma.urls_untrusted'
        return self.get_response(request)


class WaffleWithCookieDomainMiddleware(WaffleMiddleware):
    """
    The waffle.middleware.WaffleMiddleware class does not yet provide a way
    way to configure the domain of the cookies it adds to the response. This
    class is a simple wrapper around the waffle.middleware.WaffleMiddleware
    class, and it simply sets the domain of all cookies added to the response
    by waffle.middleware.WaffleMiddleware. The domain is set to the value
    configured in settings.WAFFLE_COOKIE_DOMAIN.
    """
    def process_response(self, request, response):
        keys_before = frozenset(response.cookies.keys())
        try:
            response = super(WaffleWithCookieDomainMiddleware,
                             self).process_response(request, response)
        finally:
            keys_after = frozenset(response.cookies.keys())
            for key in (keys_after - keys_before):
                response.cookies[key]['domain'] = settings.WAFFLE_COOKIE_DOMAIN
        return response
