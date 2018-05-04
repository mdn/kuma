import pytest

from django.conf import settings

from .test_locale_middleware import WEIGHTED_ACCEPT_CASES
from ..urlresolvers import get_best_language


@pytest.mark.parametrize('accept_language,locale', WEIGHTED_ACCEPT_CASES)
def test_get_best_language(accept_language, locale):
    best = get_best_language(accept_language)
    assert best == locale


@pytest.mark.parametrize("locale", settings.RTL_LANGUAGES)
def test_rtl_languages(locale):
    """Check that each RTL language is also a supported locale."""
    assert locale in settings.ENABLED_LOCALES


@pytest.mark.parametrize("alias,locale", settings.LOCALE_ALIASES.items())
def test_locale_aliases(alias, locale):
    """Check that each locale alias matches a supported locale."""
    assert alias not in settings.ENABLED_LOCALES
    assert locale in settings.ENABLED_LOCALES
