import contextlib
from urlparse import urljoin

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import urlresolvers
from django.http import (HttpResponseForbidden,
                         HttpResponsePermanentRedirect,
                         HttpResponseRedirect)
from django.middleware.locale import (
    LocaleMiddleware as DjangoLocaleMiddleware)
from django.utils import translation
from django.utils.encoding import iri_to_uri, smart_str
from django.utils.six.moves.urllib.parse import (
    urlencode, urlsplit, urlunsplit)
from whitenoise.middleware import WhiteNoiseMiddleware

from .decorators import add_shared_cache_control
from .i18n import django_language_code_to_kuma
from .utils import is_untrusted
from .views import handler403


class LangSelectorMiddleware(object):
    """
    Redirect requests with a ?lang= parameter.

    This should appear higher than LocaleMiddleware in the middleware list.
    """

    def process_request(self, request):
        """Redirect if ?lang query parameter is valid."""
        query_lang = request.GET.get('lang')
        if query_lang not in dict(settings.LANGUAGES):
            # Invalid language requested, don't redirect
            return

        # Check if the requested language is already embedded in URL
        language = translation.get_language_from_request(
            request, check_path=True)
        if language == query_lang:
            # Language is already requested language, don't redirect
            return

        script_prefix = urlresolvers.get_script_prefix()
        lang_prefix = '%s%s/' % (script_prefix, language)
        full_path = request.get_full_path()  # Includes querystring
        old_path = urlsplit(full_path).path
        new_prefix = '%s%s/' % (script_prefix, query_lang)
        if full_path.startswith(lang_prefix):
            new_path = old_path.replace(lang_prefix, new_prefix, 1)
        else:
            new_path = old_path.replace(script_prefix, new_prefix, 1)

        # Redirect to same path with requested language and without ?lang
        new_query = dict((smart_str(k), v) for
                         k, v in request.GET.iteritems() if k != 'lang')
        new_querystring = urlencode(sorted(new_query.items()))
        new_url = urlunsplit((
            request.scheme,
            request.get_host(),
            new_path,
            new_querystring,
            ''  # Fragment / Anchor
        ))
        response = HttpResponseRedirect(new_url)
        add_shared_cache_control(response)
        return response


class LocaleStandardizerMiddleware(object):
    """
    Convert 404s with legacy locales to redirects.

    This should appear higher than LocaleMiddleware in the middleware list.
    """

    def process_response(self, request, response):
        """
        Convert 404s with legacy into redirects to language-specific URLs.

        Differences:
        * Redirected URL uses Kuma language code
        """
        if response.status_code != 404:
            return response

        language_from_path = translation.get_language_from_path(request.path_info)
        literal_from_path = request.path_info.split('/')[1]
        fixed_locale = None
        match = literal_from_path == language_from_path
        lower_match = literal_from_path.lower() == language_from_path.lower()
        if lower_match and (language_from_path != literal_from_path):
            # Language code is a lower-case match for a known locale
            fixed_locale = language_from_path
        elif literal_from_path in settings.LOCALE_ALIASES:
            # Language code is a known general -> specific locale
            fixed_locale = settings.LOCALE_ALIASES[literal_from_path]
        elif not match and literal_from_path.startswith(language_from_path):
            # Language code is a specific locale (fr vs fr-FR)
            fixed_locale = language_from_path

        if fixed_locale:
            # Replace the 404 with a redirect to the fixed locale
            fixed_url = "%s://%s%s" % (
                request.scheme,
                request.get_host(),
                request.get_full_path().replace(literal_from_path,
                                                fixed_locale,
                                                1)
            )
            redirect_response = HttpResponseRedirect(fixed_url)
            add_shared_cache_control(redirect_response)
            return redirect_response
        else:
            # No language fixup found, return the 404
            return response


class LocaleMiddleware(DjangoLocaleMiddleware):
    """
    Override the base Django LocaleMiddleware with custom processing for Kuma.

    Differences:
    * Skip locale detection for known non-localized paths
    * Use Kuma language codes (en-US) instead of Django's (en-us)
    * Don't include "Vary: Accept-Language" header
    * Add caching headers to locale redirects
    """

    def process_request(self, request):
        """
        Determine the language code for the request.

        Differences:
        * Skip language detection (which adds a Vary header) if the path
          is a known non-localized path.
        * Use Kuma language codes (en-US) not Django (en-us)
        """
        # If the path is a known non-locale path, skip checks
        if not self.is_locale_path(request):
            request.LANGUAGE_CODE = settings.LANGUAGE_CODE
            return

        # Call Django's LocaleMiddleware to detect the language, activate it,
        # and set request.LANGUAGE_CODE, based on Django's language code
        response = super(LocaleMiddleware, self).process_request(request)

        # Replace Django's language code w/ Kuma's, if needed
        dj_language_code = request.LANGUAGE_CODE
        kuma_language_code = django_language_code_to_kuma(dj_language_code)
        if dj_language_code != kuma_language_code:
            translation.activate(kuma_language_code)
            request.LANGUAGE_CODE = kuma_language_code

        return response

    def is_locale_path(self, request):
        """Return True if the request path is localized path."""
        path = request.path_info.lstrip('/')
        for pattern in settings.LANGUAGE_URL_IGNORED_PATHS:
            if path.startswith(pattern):
                return False
        return True

    def process_response(self, request, response):
        """
        Convert 404s into redirects to language-specific URLs.

        Differences:
        * Use Kuma language code in locale redirect
        * Add caching headers to locale redirect
        * Delete Vary: Acceot-Language from headers
        """
        was_404 = response.status_code == 404

        # Django's process_response may add language redirect
        response = super(LocaleMiddleware, self).process_response(request,
                                                                  response)
        is_redirect = isinstance(response, self.response_redirect_class)

        # Process language redirects
        if is_redirect and was_404:
            # Use Kuma language code, not Django's, in language redirect
            language_url = response['Location']
            url_parts = urlsplit(language_url)
            path = url_parts.path
            dj_language = url_parts.path.split('/')[1]
            kuma_language = django_language_code_to_kuma(dj_language)
            if dj_language != kuma_language:
                new_path = path.replace(dj_language, kuma_language, 1)
                new_url = urlunsplit((
                    url_parts.scheme, url_parts.netloc, new_path,
                    url_parts.query, url_parts.fragment))
                response = self.response_redirect_class(new_url)

            # Add caching headers
            add_shared_cache_control(response)

        # Drop Vary: Accept-Language
        if (response.has_header('Vary') and
                response['Vary'] == 'Accept-Language'):
            del response['Vary']

        return response


class Forbidden403Middleware(object):
    """
    Renders a 403.html page if response.status_code == 403.
    """

    def process_response(self, request, response):
        if isinstance(response, HttpResponseForbidden):
            return handler403(request)
        # If not 403, return response unmodified
        return response


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
        if (response.status_code == 404 and
                request.path_info.endswith('/') and
                not is_valid_path(request, request.path_info) and
                is_valid_path(request, request.path_info[:-1])):
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


class SetRemoteAddrFromForwardedFor(object):
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1.
    """

    def process_request(self, request):
        try:
            forwarded_for = request.META['HTTP_X_FORWARDED_FOR']
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # The client's IP will be the first one.
            forwarded_for = forwarded_for.split(',')[0].strip()
            request.META['REMOTE_ADDR'] = forwarded_for


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


class RestrictedEndpointsMiddleware(object):

    def process_request(self, request):
        """
        Restricts the accessible endpoints based on the host.
        """
        if settings.ENABLE_RESTRICTIONS_BY_HOST and is_untrusted(request):
            request.urlconf = 'kuma.urls_untrusted'


class RestrictedWhiteNoiseMiddleware(WhiteNoiseMiddleware):

    def process_request(self, request):
        """
        Restricts the use of WhiteNoiseMiddleware based on the host.
        """
        if settings.ENABLE_RESTRICTIONS_BY_HOST and is_untrusted(request):
            return None
        return super(RestrictedWhiteNoiseMiddleware, self).process_request(
            request
        )


class LegacyDomainRedirectsMiddleware(object):

    def process_request(self, request):
        """
        Permanently redirects all requests from legacy domains.
        """
        if request.get_host() in settings.LEGACY_HOSTS:
            return HttpResponsePermanentRedirect(
                urljoin(settings.SITE_URL, request.get_full_path())
            )
        return None
