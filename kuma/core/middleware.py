import contextlib
import urllib
from urlparse import urljoin

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import get_script_prefix, resolve, Resolver404
from django.http import (HttpResponseForbidden,
                         HttpResponsePermanentRedirect,
                         HttpResponseRedirect)
from django.utils import translation
from django.utils.encoding import iri_to_uri, smart_str
from django.utils.six.moves.urllib.parse import (urlencode, urlsplit,
                                                 urlunsplit)
from whitenoise.middleware import WhiteNoiseMiddleware

from kuma.wiki.views.legacy import (mindtouch_to_kuma_redirect,
                                    mindtouch_to_kuma_url)

from .decorators import add_shared_cache_control
from .i18n import (get_language,
                   get_language_from_path,
                   get_language_from_request)
from .urlresolvers import Prefixer, set_url_prefixer, split_path
from .utils import is_untrusted, urlparams
from .views import handler403


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
        lang = request.GET.get('lang')

        if lang in dict(settings.LANGUAGES):
            # Blank out the locale so that we can set a new one. Remove lang
            # from the query params so we don't have an infinite loop.
            prefixer.locale = ''
            new_path = prefixer.fix(prefixer.shortened_path)
            query = dict((smart_str(k), v) for
                         k, v in request.GET.iteritems() if k != 'lang')

            # Never use HttpResponsePermanentRedirect here.
            # Its a temporary redirect and should return with http 302, not 301
            response = HttpResponseRedirect(urlparams(new_path, **query))
            add_shared_cache_control(response)
            return response

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponseRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, _ = split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            add_shared_cache_control(response)
            return response

        request.path_info = '/' + prefixer.shortened_path
        request.LANGUAGE_CODE = prefixer.locale or settings.LANGUAGE_CODE
        # prefixer.locale can be '', but we need a real locale code to activate
        # otherwise the request uses the previously handled request's
        # translations.
        translation.activate(prefixer.locale or settings.LANGUAGE_CODE)

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
        language = get_language_from_request(request)
        script_prefix = get_script_prefix()
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
        """Convert 404s into redirects to language-specific URLs."""

        if response.status_code != 404:
            return response

        language_from_path = get_language_from_path(request.path_info)
        if not language_from_path:
            # 404 URLs without locale prefixes should remain 404s
            return response

        literal_from_path = request.path_info.split('/')[1]
        fixed_locale = None
        match = literal_from_path == language_from_path
        lower_match = literal_from_path.lower() == language_from_path.lower()
        if lower_match and (language_from_path != literal_from_path):
            # Language code is a lower-case match for a known locale
            fixed_locale = language_from_path
        elif literal_from_path.lower() in settings.LOCALE_ALIASES:
            # Language code is a known general -> specific locale
            fixed_locale = settings.LOCALE_ALIASES[literal_from_path.lower()]
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


class LocaleMiddleware(object):
    """
    This is a very simple middleware that parses a request
    and decides what translation object to install in the current
    thread context. This allows pages to be dynamically
    translated to the language the user desires (if the language
    is available, of course).

    Based on Django 1.8.19's LocaleMiddleware from
    django/middleware/locale.py, with changes:

    * Assume that locale prefixes are in use
    * Use Kuma language codes (en-US) instead of Django's (en-us)
    * Use Kuma-prefered locales (zn-CN) instead of Django's (zn-Hans)
    * Don't include "Vary: Accept-Language" header
    * Add caching headers to locale redirects
    """
    response_redirect_class = HttpResponseRedirect

    def process_request(self, request):
        """Activate the language, based on the request."""
        language = get_language_from_request(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language

    def process_response(self, request, response):
        """Add Content-Language, convert some 404s to locale redirects."""
        language = get_language()
        language_from_path = get_language_from_path(request.path_info)
        if response.status_code == 404 and not language_from_path:
            language_path = '/%s%s' % (language, request.path_info)
            path_valid = is_valid_path(request, language_path)
            if (not path_valid and settings.APPEND_SLASH and
                    not language_path.endswith('/')):
                path_valid = is_valid_path(request, "%s/" % language_path)

            if path_valid:
                script_prefix = get_script_prefix()
                language_url = "%s://%s%s" % (
                    request.scheme,
                    request.get_host(),
                    # insert language after the script prefix and before the
                    # rest of the URL
                    request.get_full_path().replace(
                        script_prefix,
                        '%s%s/' % (script_prefix, language),
                        1
                    )
                )
                redirect = self.response_redirect_class(language_url)
                add_shared_cache_control(redirect)
                return redirect

        # No views set this header, so the middleware always sets it. The code
        # could be replaced with an assertion, but that would deviate from
        # Django's version, and make the code brittle, so using a pragma
        # instead. And a long comment.
        if 'Content-Language' not in response:  # pragma: no cover
            response['Content-Language'] = language
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
        match = resolve(path, urlconf)
        if match.func == mindtouch_to_kuma_redirect:
            # mindtouch_to_kuma_redirect matches everything.
            # Check if it would return a redirect or 404.
            url = mindtouch_to_kuma_url(request.LANGUAGE_CODE,
                                        match.kwargs['path'])
            return bool(url)
        else:
            return True
    except Resolver404:
        # mindtouch_to_kuma_redirect matches everything, so this branch is
        # not exercised in tests, and possibly not in production.
        return False


class RemoveSlashMiddleware(object):
    """
    Middleware that tries to remove a trailing slash if there was a 404.

    If the response is a 404 because url resolution failed, we'll look for a
    better url without a trailing slash.

    This middleware only processes non-locale URLs. Locale-prefixed URLs are
    converted to redirects in LocaleMiddleware.
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
