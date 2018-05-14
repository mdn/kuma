"""
Customizations of Django i18n functions for Kuma.

Django language code is lower case, like 'en-us'.
Kuma uses mixed case language codes, like 'en-US'.
"""
import re

from django.apps import apps
from django.conf import settings
from django.conf.locale import LANG_INFO
from django.core.urlresolvers import (
    LocaleRegexURLResolver as DjangoLocaleRegexURLResolver)
from django.utils import lru_cache, translation
from django.utils.six import string_types
from django.utils.translation.trans_real import (
    check_for_language, get_languages, language_code_prefix_re,
    language_code_re, parse_accept_lang_header)


def django_language_code_to_kuma(lang_code):
    """
    Convert Django language code to Kuma language code.

    Django uses lower-case codes like en-us.
    Mozilla uses mixed-case codes like en-US.
    """
    return settings.LANGUAGE_URL_MAP.get(lang_code, lang_code)


def kuma_language_code_to_django(lang_code):
    """
    Convert Kuma language code to Django.

    Django uses lower-case codes like en-us.
    Mozilla uses mixed-case codes like en-US.
    """
    return lang_code.lower()


def get_language():
    """Get current language in Kuma format"""
    return django_language_code_to_kuma(translation.get_language())


@lru_cache.lru_cache(maxsize=1000)
def get_supported_language_variant(raw_lang_code):
    """
    Returns the language-code that's listed in supported languages, possibly
    selecting a more generic variant. Raises LookupError if nothing found.

    If `strict` is False (the default), the function will look for an alternative
    country-specific variant when the currently checked is not found.

    lru_cache should have a maxsize to prevent from memory exhaustion attacks,
    as the provided language codes are taken from the HTTP request. See also
    <https://www.djangoproject.com/weblog/2007/oct/26/security-fix/>.

    Based on Django 1.8.18's get_supported_language_variant from
    django/utils/translation/trans_real.py, with some changes:

    * Language code can also be a Kuma language code
    * Return Kuma languge codes
    * Always allow fallback to fuzzy matching (zh-CHS gets zh-CN)
    """
    if raw_lang_code:
        lang_code = kuma_language_code_to_django(raw_lang_code)

        # Check for known override
        if lang_code in settings.LOCALE_ALIASES:
            return settings.LOCALE_ALIASES[lang_code]

        # If 'fr-ca' is not supported, try special fallback or language-only 'fr'.
        possible_lang_codes = [lang_code]
        try:
            possible_lang_codes.extend(LANG_INFO[lang_code]['fallback'])
        except KeyError:
            pass
        generic_lang_code = lang_code.split('-')[0]
        possible_lang_codes.append(generic_lang_code)
        raw_supported_lang_codes = get_languages()
        supported_lang_codes = [kuma_language_code_to_django(lang)
                                for lang in raw_supported_lang_codes]

        # Look for exact match
        for code in possible_lang_codes:
            if code in supported_lang_codes and check_for_language(code):
                return django_language_code_to_kuma(code)
        # If fr-fr is not supported, try fr-ca.
        for supported_code in supported_lang_codes:
            if supported_code.startswith(generic_lang_code + '-'):
                return django_language_code_to_kuma(supported_code)
    raise LookupError(raw_lang_code)


def get_language_from_path(path):
    """
    Returns the language-code if there is a valid language-code
    found in the `path`.

    If `strict` is False (the default), the function will look for an alternative
    country-specific variant when the currently checked is not found.

    Based on Django 1.8.18's get_language_from_path from
    django/utils/translation/trans_real.py, with some changes:

    * None yet.
    """
    regex_match = language_code_prefix_re.match(path)
    if not regex_match:
        return None
    lang_code = regex_match.group(1)
    try:
        return get_supported_language_variant(lang_code)
    except LookupError:
        return None


def get_language_from_request(request):
    """
    Analyzes the request to pick the language for the request.

    Based on Django 1.8.19's get_language_from_request from
    django/utils/translation/trans_real.py, with some changes:

    * Always check the path
    * Don't check session language
    """
    # The (valid) locale in the URL wins
    lang_code = get_language_from_path(request.path_info)
    if lang_code is not None:
        return lang_code

    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    try:
        return get_supported_language_variant(lang_code)
    except LookupError:
        pass

    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in parse_accept_lang_header(accept):
        if accept_lang == '*':
            break

        if not language_code_re.search(accept_lang):  # pragma: no cover
            # Check added with a security fix:
            # https://www.djangoproject.com/weblog/2007/oct/26/security-fix/
            # It is unclear how to trigger this branch, so skipping coverage.
            continue

        try:
            return get_supported_language_variant(accept_lang)
        except LookupError:
            continue

    # Fallback to default settings.LANGUAGE_CODE.
    # Django supports a case when LANGUAGE_CODE is not in LANGUAGES
    # (see https://github.com/django/django/pull/824). but our LANGUAGE_CODE is
    # always in LANGUAGES.
    assert settings.LANGUAGE_CODE == settings.LANGUAGES[0][0]
    return settings.LANGUAGE_CODE


class LocaleRegexURLResolver(DjangoLocaleRegexURLResolver):
    """
    A URL resolver that always matches the active language code as URL prefix.

    Rather than taking a regex argument, we just override the ``regex``
    function to always return the active language-code as regex.

    Based on 1.8.19, django.core.urlresolvers.LocaleRegexURLResolver.
    Differences:
    * Use Kuma language code in URL pattern.
    """

    @property
    def regex(self):
        language_code = get_language()
        if language_code not in self._regex_dict:
            regex_compiled = re.compile('^%s/' % language_code, re.UNICODE)
            self._regex_dict[language_code] = regex_compiled
        return self._regex_dict[language_code]


def i18n_patterns(*args):
    """
    Adds the language code prefix to every URL pattern within this
    function. This may only be used in the root URLconf, not in an included
    URLconf.

    Based on 1.8.19, django.conf.urls.i18n.i18n_patterns.
    Differences:
    * Assert that we're not using deprecated prefix parameter.
    * Assert USE_I18N is set.
    """
    assert args and not isinstance(args[0], string_types)
    assert settings.USE_I18N
    return [LocaleRegexURLResolver(list(args))]


def get_language_mapping():
    return apps.get_app_config('core').language_mapping
