"""
Customizations of Django i18n functions for Kuma.

Django language code is lower case, like 'en-us'.
Kuma language code is mixed case, like 'en-US'.
"""

from functools import lru_cache

from django.apps import apps
from django.conf import settings
from django.conf.locale import LANG_INFO
from django.utils import translation
from django.utils.translation.trans_real import (
    check_for_language,
    get_languages as _django_get_languages,
    language_code_prefix_re,
    language_code_re,
    parse_accept_lang_header,
)
from jinja2 import nodes
from jinja2.ext import Extension


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
    """Returns the currently selected language as a Kuma language code."""
    return django_language_code_to_kuma(translation.get_language())


@lru_cache()
def get_django_languages():
    """
    Cache of settings.LANGUAGES, with Django keys, for easy lookups by key.

    This would be the same as Django's get_languages, if we were using Django
    language codes.
    """
    return {
        kuma_language_code_to_django(locale): name
        for locale, name in settings.LANGUAGES
    }


def get_kuma_languages():
    """
    Cache of settings.LANGUAGES, with Kuma keys, for easy lookups by key.

    This is identical to Django's get_languages, but the name makes it
    clearer that Kuma language codes are used.
    """
    return _django_get_languages()


@lru_cache(maxsize=1000)
def get_supported_language_variant(raw_lang_code):
    """
    Returns the language-code that's listed in supported languages, possibly
    selecting a more generic variant. Raises LookupError if nothing found.

    The function will look for an alternative country-specific variant when the
    currently checked language code is not found. In Django, this behaviour can
    be avoided with the strict=True parameter, removed in this code.

    lru_cache should have a maxsize to prevent from memory exhaustion attacks,
    as the provided language codes are taken from the HTTP request. See also
    <https://www.djangoproject.com/weblog/2007/oct/26/security-fix/>.

    Based on Django 1.11.16's get_supported_language_variant from
    django/utils/translation/trans_real.py, with changes:

    * Language code can also be a Kuma language code
    * Return Kuma languge codes
    * Force strict=False to always allow fuzzy matching (zh-CHS gets zh-CN)
    """
    if raw_lang_code:
        # Kuma: Convert Kuma to Django language code
        lang_code = kuma_language_code_to_django(raw_lang_code)

        # Kuma: Check for known override
        if lang_code in settings.LOCALE_ALIASES:
            return settings.LOCALE_ALIASES[lang_code]

        # If 'fr-ca' is not supported, try special fallback or language-only 'fr'.
        possible_lang_codes = [lang_code]
        try:
            possible_lang_codes.extend(LANG_INFO[lang_code]["fallback"])
        except KeyError:
            pass
        generic_lang_code = lang_code.split("-")[0]
        possible_lang_codes.append(generic_lang_code)
        supported_lang_codes = get_django_languages()

        # Look for exact match
        for code in possible_lang_codes:
            if code in supported_lang_codes and check_for_language(code):
                # Kuma: Convert to Kuma language code
                return django_language_code_to_kuma(code)
        # If fr-fr is not supported, try fr-ca.
        for supported_code in supported_lang_codes:
            if supported_code.startswith(generic_lang_code + "-"):
                # Kuma: Convert to Kuma language code
                return django_language_code_to_kuma(supported_code)
    raise LookupError(raw_lang_code)


def get_language_from_path(path):
    """
    Returns the language-code if there is a valid language-code
    found in the `path`.

    Based on Django 1.11.16's get_language_from_path from
    django/utils/translation/trans_real.py, with changes:

    * Don't accept or pass strict parameter (assume strict=False).
    * Use our customized get_supported_language_variant().
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
    Analyzes the request to find what language the user wants the system to
    show. Only languages listed in settings.LANGUAGES are taken into account.
    If the user requests a sublanguage where we have a main language, we send
    out the main language.

    If there is a language code in the URL path prefix, then it is selected as
    the request language and other methods (language cookie, Accept-Language
    header) are skipped. In Django, the URL path prefix can be skipped with the
    check_path=False parameter, removed in this code.

    Based on Django 1.11.16's get_language_from_request from
    django/utils/translation/trans_real.py, with changes:

    * Always check the path.
    * Don't check session language.
    * Use LANGUAGE_CODE as the fallback language code, instead of passing it
      through get_supported_language_variant first.
    """
    # Kuma: Always use the URL's language (force check_path=True)
    lang_code = get_language_from_path(request.path_info)
    if lang_code is not None:
        return lang_code

    # Kuma: Skip checking the session-stored language via LANGUAGE_SESSION_KEY

    # Use the (valid) language cookie override
    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    try:
        return get_supported_language_variant(lang_code)
    except LookupError:
        pass

    # Pick the closest langauge based on the Accept Language header
    accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for accept_lang, unused in parse_accept_lang_header(accept):
        if accept_lang == "*":
            break

        # Kuma: Assert accept_lang fits the language code pattern
        # The regex check was added with a security fix:
        # https://www.djangoproject.com/weblog/2007/oct/26/security-fix/
        # In the Django version, non-matching accept_lang codes are skipped.
        # However, it doesn't seem possible for parse_accept_lang_header to
        # return codes that would fail this check.
        # The assertion keeps the security aspect, and gives us an opportunity
        # to add a test case to Kuma and Django.
        assert language_code_re.search(accept_lang)

        try:
            return get_supported_language_variant(accept_lang)
        except LookupError:
            continue

    # Kuma: Fallback to default settings.LANGUAGE_CODE.
    # Django supports a case when LANGUAGE_CODE is not in LANGUAGES
    # (see https://github.com/django/django/pull/824). but our LANGUAGE_CODE is
    # always the first entry in LANGUAGES.
    return settings.LANGUAGE_CODE


def get_language_mapping():
    return apps.get_app_config("core").language_mapping


def activate_language_from_request(request):
    """
    Activate the language, based on the request.

    Based on Django 1.11.16's LocaleMiddleware.process_request from
    django/middleware/locale, with these changes:

    * Assume language prefix patterns are used, with no implied default
      language (prefix_default_language=True)
    * Use Kuma's language selection via our get_language_from_request.
    * Skip get_language_from_path, since used to determine if implied
      default language is used.
    * Set request.LANGUAGE_CODE to Kuma language code via get_language.

    This is in its own function so it can be called from the
    kuma.search tests to set the request language.
    """
    language = get_language_from_request(request)
    translation.activate(language)
    request.LANGUAGE_CODE = get_language()


class TranslationExtension(Extension):
    """
    Provide a Jinja2 tag like Django's {% translation %} block

    Usage:

    {% translation 'en-US' %}
      <p>_('This string is translatable, but displayed in English.')</p>
    {% endtranslation %}

    See Django documentation for details:
    https://docs.djangoproject.com/en/1.11/topics/i18n/translation/#switching-language-in-templates

    Jinja2 has a parsing phase and then a rendering phase. This parses the {%
    translation %} block as a CallBlock node that will override the translation
    at render time. It is very similar to the example in the docs:

    http://jinja.pocoo.org/docs/2.10/extensions/#module-jinja2.ext
    """

    tags = {"translation"}

    def parse(self, parser):
        """Parse a stream starting with {% translation %}."""
        # Get the line number and desired language
        lineno = next(parser.stream).lineno
        block_language = parser.parse_expression()

        # Parse the block body until {% endtranslation %}
        body = parser.parse_statements(["name:endtranslation"], drop_needle=True)

        # Return a node that will render body in the desired translation
        return nodes.CallBlock(
            self.call_method("_override", [block_language]), [], [], body
        ).set_lineno(lineno)

    def _override(self, block_language, caller):
        """Render a {% translation %} block with the requested language."""
        with translation.override(block_language):
            value = caller()
        return value
