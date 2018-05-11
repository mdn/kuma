import pytest

from django.conf import settings


@pytest.mark.parametrize("locale", settings.RTL_LANGUAGES)
def test_rtl_languages(locale):
    """Check that each RTL language is also a supported locale."""
    assert locale in settings.ENABLED_LOCALES


@pytest.mark.parametrize("alias,locale", settings.LOCALE_ALIASES.items())
def test_locale_aliases(alias, locale):
    """Check that each locale alias matches a supported locale."""
    assert alias not in settings.ENABLED_LOCALES
    assert alias == alias.lower()
    assert locale in settings.ENABLED_LOCALES
