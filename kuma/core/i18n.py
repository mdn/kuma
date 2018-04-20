"""
Customizations of Django i18n functions for Kuma.

Django language code is lower case, like 'en-us'.
Kuma uses mixed case language codes, like 'en-US'.
"""
import re

from django.apps import apps
from django.conf import settings
from django.core.urlresolvers import (
    LocaleRegexURLResolver as DjangoLocaleRegexURLResolver)
from django.utils import translation
from django.utils.six import string_types


def django_language_code_to_kuma(lang_code):
    """
    Convert Django language code to Kuma language code.

    Django uses lower-case codes like en-us.
    Mozilla uses mixed-case codes like en-US.
    """
    return settings.LANGUAGE_URL_MAP.get(lang_code, lang_code)


def get_language():
    """Get current language in Kuma format"""
    return django_language_code_to_kuma(translation.get_language())


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
