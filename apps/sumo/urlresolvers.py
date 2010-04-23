from django.conf import settings
from django.core.urlresolvers import reverse as django_reverse
from django.utils.thread_support import currentThread
from django.utils.translation.trans_real import parse_accept_lang_header


# Thread-local storage for URL prefixes. Access with (get|set)_url_prefix.
_prefixes = {}


def set_url_prefix(prefix):
    """Set the ``prefix`` for the current thread."""
    _prefixes[currentThread()] = prefix


def get_url_prefix():
    """Get the prefix for the current thread, or None."""
    return _prefixes.get(currentThread())


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None):
    """Wraps Django's reverse to prepend the correct locale."""
    prefixer = get_url_prefix()

    if prefixer:
        prefix = prefix or '/'
    url = django_reverse(viewname, urlconf, args, kwargs, prefix)
    if prefixer:
        return prefixer.fix(url)
    else:
        return url


def find_supported(test):
    return [settings.LANGUAGE_URL_MAP[x] for
            x in settings.LANGUAGE_URL_MAP if
            x.split('-', 1)[0] == test.lower().split('-', 1)[0]]


class Prefixer(object):

    def __init__(self, request):
        self.request = request
        split = self.split_path(request.path_info)
        self.locale, self.shortened_path = split

    def split_path(self, path_):
        """
        Split the requested path into (locale, path).

        locale will be empty if it isn't found.
        """
        path = path_.lstrip('/')

        # Use partitition instead of split since it always returns 3 parts
        first, _, rest = path.partition('/')

        lang = first.lower()
        if lang in settings.LANGUAGE_URL_MAP:
            return settings.LANGUAGE_URL_MAP[lang], rest
        else:
            supported = find_supported(first)
            if len(supported):
                return supported[0], rest
            else:
                return '', path

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
            ranked_languages = parse_accept_lang_header(
                self.request.META['HTTP_ACCEPT_LANGUAGE'])

            # Do we support or remap their locale?
            supported = [lang[0] for lang in ranked_languages if lang[0]
                        in settings.LANGUAGE_URL_MAP]

            # Do we support a less specific locale? (xx-YY -> xx)
            if not len(supported):
                for lang in ranked_languages:
                    supported = find_supported(lang[0])
                    if supported:
                        break

            if len(supported):
                return settings.LANGUAGE_URL_MAP[supported[0].lower()]

        return settings.LANGUAGE_CODE

    def fix(self, path):
        path = path.lstrip('/')
        url_parts = [self.request.META['SCRIPT_NAME']]

        if path.partition('/')[0] not in settings.SUPPORTED_NONLOCALES:
            locale = self.locale if self.locale else self.get_language()
            url_parts.append(locale)

        url_parts.append(path)

        return '/'.join(url_parts)
