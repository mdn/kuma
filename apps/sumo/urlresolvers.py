import threading

from django.conf import settings
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse as django_reverse
from django.utils.translation.trans_real import parse_accept_lang_header


# Thread-local storage for URL prefixes. Access with (get|set)_url_prefix.
_locals = threading.local()


def get_best_language(accept_lang):
    """Given an Accept-Language header, return the best-matching language."""

    ranked = parse_accept_lang_header(accept_lang)
    return find_supported(ranked)


def set_url_prefixer(prefixer):
    """Set the Prefixer for the current thread."""
    _locals.prefixer = prefixer


def get_url_prefixer():
    """Get the Prefixer for the current thread, or None."""
    return getattr(_locals, 'prefixer', None)


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
            force_locale=False, locale=None):
    """Wraps Django's reverse to prepend the correct locale.

    force_locale -- Ordinarily, if get_url_prefixer() returns None, we return
        an unlocalized URL, which will be localized via redirect when visited.
        Set force_locale to True to force the insertion of a default locale
        when there is no set prefixer. If you are writing a test and simply
        wish to avoid LocaleURLMiddleware's initial 301 when passing in an
        unprefixed URL, it is probably easier to substitute LocalizingClient
        for any uses of django.test.client.Client and forgo this kwarg.

    locale -- By default, reverse prepends the current locale (if set) or
        the default locale if force_locale == True. To override this behavior
        and have it prepend a different locale, pass in the locale parameter
        with the desired locale. When passing a locale, the force_locale is
        not used and is implicitly True.

    """
    if locale:
        prefixer = Prefixer(locale=locale)
    else:
        prefixer = get_url_prefixer()
        if not prefixer and force_locale:
            prefixer = Prefixer()

    if prefixer:
        prefix = prefix or '/'
    url = django_reverse(viewname, urlconf, args, kwargs, prefix)

    # HACK: We rewrite URLs in apps/wiki/middleware.py, but don't have a
    # concept for pluggable middleware in reverse() as far as I know. So, this
    # is an app-specific override. ABSOLUTE_URL_OVERRIDES doesn't really do the
    # trick.
    #
    # See apps/wiki/tests/test_middleware.py for a test exercising this hack.
    if url.startswith('/docs/'):
        # HACK: Import here, because otherwise it's a circular reference
        from wiki.models import DocumentZone
        # Work out a current locale, from some source.
        zone_locale = locale
        if not zone_locale: 
            if prefixer:
                zone_locale = prefixer.locale
            else:
                zone_locale = settings.WIKI_DEFAULT_LANGUAGE
        # Get DocumentZone remaps for the current locale.
        remaps = DocumentZone.objects.get_url_remaps(zone_locale)
        for remap in remaps:
            if url.startswith(remap['original_path']):
                url = url.replace(remap['original_path'],
                                  remap['new_path'], 1)
                break

    if prefixer:
        return prefixer.fix(url)
    else:
        return url


def find_supported(ranked):
    """Given a ranked language list, return the best-matching locale."""
    langs = dict(settings.LANGUAGE_URL_MAP)
    for lang, _ in ranked:
        lang = lang.lower()
        if lang in langs:
            return langs[lang]
        # Add derived language tags to the end of the list as a fallback.
        pre = '-'.join(lang.split('-')[0:-1])
        if pre:
            ranked.append((pre, None))
    # Couldn't find any acceptable locale.
    return False


def split_path(path):
    """
    Split the requested path into (locale, path).

    locale will be empty if it isn't found.
    """
    path = path.lstrip('/')

    # Use partition instead of split since it always returns 3 parts
    first, _, rest = path.partition('/')

    # Treat locale as a single-item ranked list.
    lang = find_supported([(first, 1.0)])

    if lang:
        return lang, rest
    else:
        return '', path


class Prefixer(object):
    def __init__(self, request=None, locale=None):
        """If request is omitted, fall back to a default locale."""
        self.request = request or RequestFactory(REQUEST_METHOD='bogus').request()
        self.locale, self.shortened_path = split_path(self.request.path_info)
        if locale:
            self.locale = locale

    def get_language(self):
        """
        Return a locale code we support on the site using the
        user's Accept-Language header to determine which is best. This
        mostly follows the RFCs but read bug 439568 for details.
        """
        if 'lang' in self.request.GET:
            lang = self.request.GET['lang'].lower()
            if lang in settings.LANGUAGE_URL_MAP:
                return settings.LANGUAGE_URL_MAP[lang]

        if self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            best = get_best_language(
                self.request.META['HTTP_ACCEPT_LANGUAGE'])
            if best:
                return best

        return settings.LANGUAGE_CODE

    def fix(self, path):
        path = path.lstrip('/')
        url_parts = [self.request.META['SCRIPT_NAME']]

        if path.partition('/')[0] not in settings.SUPPORTED_NONLOCALES:
            locale = self.locale if self.locale else self.get_language()
            url_parts.append(locale)

        url_parts.append(path)

        return '/'.join(url_parts)
