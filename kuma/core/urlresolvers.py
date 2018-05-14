from django.conf import settings
from django.core.urlresolvers import reverse as django_reverse
from django.utils import translation


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
            current_app=None, force_locale=False, locale=None, unprefixed=False):
    """Wraps Django's reverse to prepend the requested locale.

    Keyword Arguments:
    * locale - Use this locale prefix rather than the current active locale.

    Keyword Arguments passed to Django's reverse:
    * viewname
    * urlconf
    * args
    * kwargs
    * current_app

    Legacy Keyword Arguments (TODO: remove from callers)
    * prefix
    * force_locale
    * unprefixed
    """
    if locale:
        with translation.override(locale):
            return django_reverse(viewname, urlconf=urlconf, args=args,
                                  kwargs=kwargs, current_app=current_app)
    else:
        return django_reverse(viewname, urlconf=urlconf, args=args,
                              kwargs=kwargs, current_app=current_app)


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
