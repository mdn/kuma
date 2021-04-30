import pytest
from django.conf import settings
from django.urls import reverse

from . import assert_shared_cache_header


# Simple Accept-Language headers, one term
SIMPLE_ACCEPT_CASES = (
    ("", "en-US"),  # No preference gets default en-US
    ("en", "en-US"),  # Default en is en-US
    ("en-US", "en-US"),  # Exact match for default
    ("en-us", "en-US"),  # Case-insensitive match for default
    ("fr-FR", "fr"),  # Overly-specified locale gets default
    ("fr-fr", "fr"),  # Overly-specified match is case-insensitive
)
# Real-world Accept-Language headers include quality value weights
WEIGHTED_ACCEPT_CASES = (
    ("en, fr;q=0.5", "en-US"),  # English without region gets en-US
    ("en-GB, fr-FR;q=0.5", "en-US"),  # Any English gets en-US
    ("en-US, en;q=0.5", "en-US"),  # Request for en-US gets en-US
    ("fr, en-US;q=0.5", "fr"),  # Exact match of non-English language
    ("fr-FR, de-DE;q=0.5", "fr"),  # Highest locale-specific match wins
    ("fr-FR, de;q=0.5", "fr"),  # First generic match wins
    ("pt, fr;q=0.5", "pt-BR"),  # Generic Portuguese matches pt-BR
    ("pt-BR, en-US;q=0.5", "pt-BR"),  # Portuguese-Brazil matches
    ("qaz-ZZ, fr-FR;q=0.5", "fr"),  # Respect partial match on prefix
    ("qaz-ZZ, qaz;q=0.5", False),  # No matches gets default en-US
    ("zh-Hant, fr;q=0.5", "zh-TW"),  # Traditional Chinese matches zh-TW
    ("*", "en-US"),  # Any-language case gets default
)
PICKER_CASES = (
    SIMPLE_ACCEPT_CASES
    + WEIGHTED_ACCEPT_CASES
    + (("xx", "en-US"),)  # Unknown in Accept-Language gets default
)
REDIRECT_CASES = [
    ("cn", "zh-CN"),  # General to locale-specific in different general locale
    ("pt", "pt-BR"),  # General to locale-specific
    ("PT", "pt-BR"),  # It does a case-insensitive comparison
    ("fr-FR", "fr"),  # Country-specific to language-only
    ("Fr-fr", "fr"),  # It does a case-insensitive comparison
    ("en", "en-US"),  # Ensure that en redirects to en-US, case insensitive
    ("En", "en-US"),
    ("EN", "en-US"),
    ("zh-Hans", "zh-CN"),  # Django-preferred to Mozilla standard locale
    ("zh_tw", "zh-TW"),  # Underscore and capitalization fix
] + [(orig, new) for (orig, new) in SIMPLE_ACCEPT_CASES if orig != new]


def test_locale_middleware_redirect_when_not_homepage(client, db):
    """The LocaleMiddleware redirects via 302 when it's not the homepage."""
    response = client.get("/docs/Web/HTML")
    assert response.status_code == 302
    assert response["Location"] == "/en-US/docs/Web/HTML"
    assert_shared_cache_header(response)


@pytest.mark.parametrize("accept_language,locale", PICKER_CASES)
def test_locale_middleware_picker(accept_language, locale, client, db):
    """The LocaleMiddleware picks locale from the Accept-Language header."""
    response = client.get("/", HTTP_ACCEPT_LANGUAGE=accept_language)
    assert response.status_code == 301
    url_locale = locale or "en-US"
    assert response["Location"] == ("/%s/" % url_locale)
    assert_shared_cache_header(response)


@pytest.mark.parametrize("original,fixed", REDIRECT_CASES)
def test_locale_middleware_fixer(original, fixed, client, db):
    """The LocaleStandardizerMiddleware redirects non-standard locale URLs."""
    response = client.get(("/%s/" % original) if original else "/")
    if original == "":
        # LocaleMiddleware handles this case, and it's a 301 instead
        # of a 302 since it's the homepage.
        expected_status_code = 301
    else:
        expected_status_code = 302
    assert response.status_code == expected_status_code
    assert response["Location"] == "/%s/" % fixed
    assert_shared_cache_header(response)


def test_locale_middleware_fixer_confusion(client, db):
    """The LocaleStandardizerMiddleware treats unknown locales as 404s."""
    response = client.get("/xx/")
    assert response.status_code == 404


def test_locale_middleware_language_cookie(client, db):
    """The LocaleMiddleware uses the language cookie over the header."""
    client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "ja"})
    response = client.get("/", HTTP_ACCEPT_LANGUAGE="fr")
    assert response.status_code == 301
    assert response["Location"] == "/ja/"
    assert_shared_cache_header(response)


@pytest.mark.parametrize("path", ("/", "/en-US/"))
def test_lang_selector_middleware(path, client):
    """The LangSelectorMiddleware redirects on the ?lang query first."""
    client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "ja"})
    response = client.get(f"{path}?lang=fr", HTTP_ACCEPT_LANGUAGE="en;q=0.9, fr;q=0.8")
    assert response.status_code == 302
    assert response["Location"] == "/fr/"
    assert_shared_cache_header(response)


def test_lang_selector_middleware_preserves_query(root_doc, client):
    """The LangSelectorMiddleware preserves other parameters."""
    url = reverse("wiki.json")
    query = {"lang": root_doc.locale, "slug": root_doc.slug}
    response = client.get(url, query)
    assert response.status_code == 302
    expected = f"{url}?slug={root_doc.slug}"
    assert response["Location"] == expected
    assert_shared_cache_header(response)


def test_lang_selector_middleware_no_change(client, db):
    """The LangSelectorMiddleware redirects on the same ?lang query."""
    response = client.get("/fr/?lang=fr")
    assert response.status_code == 302
    assert response["Location"] == "/fr/"
    assert_shared_cache_header(response)


# Paths that were once valid, but now should 404, rather than get a second
# chance with a locale prefix.
# Subset of tests.headless.map_301.LEGACY_URLS
LEGACY_404S = (
    "/index.php",
    "/index.php?title=En/HTML/Canvas&revision=110",
    "/patches",
    "/patches/foo",
    "/web-tech",
    "/web-tech/feed/atom/",
    "/css/wiki.css",
    "/css/base.css",
)


@pytest.mark.parametrize("path", LEGACY_404S)
def test_locale_middleware_legacy_404s(client, path, db):
    """Legacy paths should be 404s, not get a locale prefix."""
    response = client.get(path)
    assert response.status_code == 404
