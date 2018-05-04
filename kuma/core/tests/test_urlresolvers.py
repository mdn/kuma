import pytest

from django.conf import settings

from ..urlresolvers import get_best_language

# Real-world Accept-Language headers include quality value weights
WEIGHTED_ACCEPT_CASES = (
    ('en, fr;q=0.5', 'en-US'),          # English without region gets en-US
    ('en-GB, fr-FR;q=0.5', 'en-US'),    # Any English gets en-US
    ('en-US, en;q=0.5', 'en-US'),       # Request for en-US gets en-US
    ('fr, en-US;q=0.5', 'fr'),          # Exact match of non-English language
    ('fr-FR, de-DE;q=0.5', 'fr'),       # Highest locale-specific match wins
    ('fr-FR, de;q=0.5', 'de'),          # Highest exact match wins
    ('ga, fr;q=0.5', 'ga-IE'),          # Generic Gaelic matches ga-IE
    ('pt, fr;q=0.5', 'pt-PT'),          # Generic Portuguese matches pt-PT
    ('pt-BR, en-US;q=0.5', 'pt-BR'),    # Portuguese-Brazil matches
    ('qaz-ZZ, fr-FR;q=0.5', 'fr'),      # Respect partial match on prefix
    ('qaz-ZZ, qaz;q=0.5', False),       # No matches gets default en-US
    ('zh-Hant, fr;q=0.5', 'zh-TW'),     # Traditional Chinese matches zh-TW
)


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
