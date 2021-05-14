from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.urls import get_script_prefix, is_valid_path
from waffle.middleware import WaffleMiddleware

from .decorators import add_shared_cache_control
from .i18n import (
    activate_language_from_request,
    get_language,
    get_language_from_path,
)


class MiddlewareBase(object):
    def __init__(self, get_response):
        self.get_response = get_response


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

        literal_from_path = request.path_info.split("/")[1]
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
        urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)

        # Kuma: assume locale-prefix patterns, including default language
        if response.status_code == 404 and not language_from_path:
            # Maybe the language code is missing in the URL? Try adding the
            # language prefix and redirecting to that URL.
            language_path = f"/{language}{request.path_info}"
            path_valid = is_valid_path(language_path, urlconf)
            print(
                f"path_valid = {path_valid}, language = {language}, language_from_path = {language_from_path}, language_path = {language_path}"
            )
            path_needs_slash = not path_valid and (
                settings.APPEND_SLASH
                and not language_path.endswith("/")
                and is_valid_path("%s/" % language_path, urlconf)
            )

            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                # Insert language after the script prefix and before the
                # rest of the URL
                language_url = request.get_full_path(
                    force_append_slash=path_needs_slash
                ).replace(script_prefix, f"{script_prefix}{language}/", 1)
                # Kuma: Add caching headers to redirect
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
        if "Content-Language" not in response:  # pragma: no cover
            response["Content-Language"] = language

        return response


class SetRemoteAddrFromForwardedFor(MiddlewareBase):
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1.
    """

    def __call__(self, request):
        try:
            forwarded_for = request.META["HTTP_X_FORWARDED_FOR"]
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # The client's IP will be the first one.
            forwarded_for = forwarded_for.split(",")[0].strip()
            request.META["REMOTE_ADDR"] = forwarded_for

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
            response = super(WaffleWithCookieDomainMiddleware, self).process_response(
                request, response
            )
        finally:
            keys_after = frozenset(response.cookies.keys())
            for key in keys_after - keys_before:
                response.cookies[key]["domain"] = settings.WAFFLE_COOKIE_DOMAIN
        return response
