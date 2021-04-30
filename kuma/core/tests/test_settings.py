"""Check that settings are consistent."""


import pytest
from django.conf import settings


def test_accepted_locales():
    """Check for a consistent ACCEPTED_LOCALES."""
    assert len(settings.ACCEPTED_LOCALES) == len(set(settings.ACCEPTED_LOCALES))
    assert settings.ACCEPTED_LOCALES[0] == settings.LANGUAGE_CODE


@pytest.mark.parametrize(
    "primary,secondary",
    (("zh-CN", "zh-TW"),),
)
def test_preferred_locale_codes(primary, secondary):
    assert settings.ACCEPTED_LOCALES.index(primary) < settings.ACCEPTED_LOCALES.index(
        secondary
    )


@pytest.mark.parametrize("alias,locale", settings.LOCALE_ALIASES.items())
def test_locale_aliases(alias, locale):
    """Check that each locale alias matches a supported locale."""
    assert alias not in settings.ACCEPTED_LOCALES
    assert alias == alias.lower()
    assert locale in settings.ACCEPTED_LOCALES
