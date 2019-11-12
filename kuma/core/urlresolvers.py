

import re

from django.conf import settings
from django.urls import (
    LocaleRegexURLResolver as DjangoLocaleRegexURLResolver,
    reverse as django_reverse)
from django.utils import translation

from .i18n import get_language


class LocaleRegexURLResolver(DjangoLocaleRegexURLResolver):
    """
    A URL resolver that always matches the active language code as URL prefix.

    Rather than taking a regex argument, we just override the ``regex``
    function to always return the active language-code as regex.

    Based on Django 1.11.16's LocaleRegexURLResolver from
    django/urls/resolvers, with changes:

    * Use Kuma language code (via get_language()) in URL pattern.
    * Assert prefix_default_language is True, so that the default locale must
      be included in the path.
    """

    @property
    def regex(self):
        language_code = get_language() or settings.LANGUAGE_CODE
        if language_code not in self._regex_dict:
            # Kuma: Do not allow an implied default language
            assert self.prefix_default_language
            regex_string = '^%s/' % language_code
            self._regex_dict[language_code] = re.compile(
                regex_string, re.UNICODE)
        return self._regex_dict[language_code]


def i18n_patterns(*urls, **kwargs):
    """
    Adds the language code prefix to every URL pattern within this
    function. This may only be used in the root URLconf, not in an included
    URLconf.

    Based on Django 1.11.16's i18n_patterns from django/conf/urls/i18n,
    with changes:

    * Assert USE_I18N is set, rather than fallback to list.
    * Assert prefix_default_language is True, so that the default locale must
      be included in the path.
    * Use our customized LocaleRegexURLResolver.
    """
    assert settings.USE_I18N
    prefix_default_language = kwargs.pop('prefix_default_language', True)
    assert not kwargs, 'Unexpected kwargs for i18n_patterns(): %s' % kwargs

    # Assumed to be True in:
    # kuma.core.i18n.activate_language_from_request
    # kuma.core.middleware.LocaleMiddleware
    assert prefix_default_language, (
        'Kuma does not support prefix_default_language=False')
    return [LocaleRegexURLResolver(list(urls),
            prefix_default_language=prefix_default_language)]


def reverse(viewname, urlconf=None, args=None, kwargs=None,
            current_app=None, locale=None):
    """Wraps Django's reverse to prepend the requested locale.
    Keyword Arguments:
    * locale - Use this locale prefix rather than the current active locale.
    Keyword Arguments passed to Django's reverse:
    * viewname
    * urlconf
    * args
    * kwargs
    * current_app
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
