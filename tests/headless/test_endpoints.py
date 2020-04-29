import re
from urllib.parse import quote, urlsplit

import pytest
from pyquery import PyQuery

from . import INDEXED_WEB_DOMAINS, request


META_ROBOTS_RE = re.compile(
    r"""(?x)    # Verbose regex mode
    <meta\s+                        # meta tag followed by whitespace
    name="robots"\s*                # name=robots
    content="(?P<content>[^"]+)"    # capture the content
    \s*>                            # end meta tag
"""
)


@pytest.fixture()
def is_indexed(site_url):
    hostname = urlsplit(site_url).netloc
    return hostname in INDEXED_WEB_DOMAINS


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    "slug",
    [
        "/en-US/promote",
        "/en-US/promote/buttons",
        "/en-US/maintenance-mode",
        "/en-US/unsubscribe/1",
        "/en-US/dashboards",
        "/en-US/dashboards/spam",
        "/en-US/dashboards/revisions",
        "/en-US/dashboards/macros",
        "/en-US/dashboards/user_lookup?user=sheppy",
        "/en-US/dashboards/topic_lookup?topic=mathml",
        "/en-US/users/account/keys",
        "/en-US/users/account/keys/new",
        "/en-US/users/account/keys/1/history",
        "/en-US/users/account/keys/1/delete",
        "/en-US/users/ban/trump",
        "/en-US/users/ban_user_and_cleanup/trump",
        "/en-US/users/ban_user_and_cleanup_summary/trump",
        "/en-US/docs/ckeditor_config.js",
        "/en-US/docs/preview-wiki-content",
        "/en-US/docs/all",
        "/en-US/docs/new?slug=test",
        "/en-US/docs/tags",
        "/en-US/docs/tag/ARIA",
        "/en-US/docs/needs-review",
        "/en-US/docs/needs-review/editorial",
        "/en-US/docs/localization-tag",
        "/en-US/docs/localization-tag/inprogress",
        "/en-US/docs/top-level",
        "/en-US/docs/with-errors",
        "/en-US/docs/without-parent",
        "/en-US/docs/templates",
        "/en-US/docs/submit_akismet_spam",
        "/en-US/docs/Web/HTML?raw",
        "/en-US/docs/Web/HTML$api",
        "/en-US/docs/Web/HTML$toc",
        "/en-US/docs/Web/HTML$edit",
        "/en-US/docs/Web/HTML$move",
        "/en-US/docs/Web/HTML$files",
        "/en-US/docs/Web/HTML$purge",
        "/en-US/docs/Web/HTML$delete",
        "/en-US/docs/Web/HTML$history",
        "/en-US/docs/Web/HTML$restore",
        "/en-US/docs/Web/HTML$locales",
        "/en-US/docs/Web/HTML$translate",
        "/en-US/docs/Web/HTML$subscribe",
        "/en-US/docs/Web/HTML$subscribe_to_tree",
        "/en-US/docs/Web/HTML$quick-review",
        "/en-US/docs/Web/HTML$revert/1293895",
        "/en-US/docs/Web/HTML$revision/1293895",
        "/en-US/docs/Web/HTML$repair_breadcrumbs",
        "/en-US/docs/Web/HTML$compare?locale=en-US&to=1299417&from=1293895",
    ],
)
def test_redirect_to_wiki(site_url, wiki_site_url, slug):
    """Ensure that these endpoints redirect to the wiki domain."""
    resp = request("get", site_url + slug)
    assert resp.status_code == 301
    assert resp.headers["location"] == wiki_site_url + slug


@pytest.mark.headless
@pytest.mark.nondestructive
def test_redirect_contribute(site_url, wiki_site_url):
    for base_url in (site_url, wiki_site_url):
        url = base_url + "/en-US/contribute/"
        resp = request("get", url)
        assert resp.status_code == 302, url
        assert resp.headers["location"] == "/en-US/payments/", url


@pytest.mark.headless
@pytest.mark.nondestructive
def test_redirect_localization_dashboard(site_url, wiki_site_url):
    for base_url in (site_url, wiki_site_url):
        url = base_url + "/en-US/dashboards/localization"
        resp = request("get", url)
        assert resp.status_code == 301, url
        assert resp.headers["location"] == "/docs/MDN/Doc_status/Overview", url


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document_json(site_url):
    url = site_url + "/en-US/docs/Web$json"
    resp = request("get", url)
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/json"
    assert resp.headers["Access-Control-Allow-Origin"] == "*"


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document(site_url, is_indexed):
    url = site_url + "/en-US/docs/Web"
    resp = request("get", url)
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "text/html; charset=utf-8"
    meta = META_ROBOTS_RE.search(resp.text)
    assert meta
    content = meta.group("content")
    if is_indexed:
        assert content == "index, follow"
    else:
        assert content == "noindex, nofollow"


@pytest.mark.headless
@pytest.mark.nondestructive
def test_user_document(site_url):
    url = site_url + "/en-US/docs/User:anonymous:uitest"
    resp = request("get", url)
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "text/html; charset=utf-8"
    meta = META_ROBOTS_RE.search(resp.text)
    assert meta
    content = meta.group("content")
    # Pages with legacy MindTouch namespaces like 'User:' never get
    # indexed, regardless of what the base url is
    assert content == "noindex, nofollow"


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document_based_redirection(site_url):
    """Ensure that content-based redirects properly redirect."""
    url = site_url + "/en-US/docs/MDN/Promote"
    resp = request("get", url)
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/en-US/docs/MDN/About/Promote"


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document_based_redirection_suppression(site_url):
    """
    Ensure that the redirect directive and not the content of the target
    page is displayed when content-based redirects are suppressed.
    """
    url = site_url + "/en-US/docs/MDN/Promote?redirect=no"
    resp = request("get", url)
    assert resp.status_code == 200
    body = PyQuery(resp.text)("#wikiArticle")
    assert body.text().startswith("REDIRECT ")
    assert body.find('a[href="/en-US/docs/MDN/About/Promote"]')


@pytest.mark.smoke
@pytest.mark.headless
@pytest.mark.nondestructive
def test_home(site_url, is_indexed):
    url = site_url + "/en-US/"
    resp = request("get", url)
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "text/html; charset=utf-8"
    meta = META_ROBOTS_RE.search(resp.text)
    assert meta
    content = meta.group("content")
    if is_indexed:
        assert content == "index, follow"
    else:
        assert content == "noindex, nofollow"


@pytest.mark.headless
@pytest.mark.nondestructive
def test_hreflang_basic(site_url):
    """Ensure that we're specifying the correct value for lang and hreflang."""
    url = site_url + "/en-US/docs/Web/HTTP"
    resp = request("get", url)
    assert resp.status_code == 200
    html = PyQuery(resp.text)
    assert html.attr("lang") == "en"
    assert html.find('head > link[hreflang="en"][href="{}"]'.format(url))


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    "uri,expected_keys",
    [
        ("/api/v1/whoami", (("waffle", ("flags", "switches", "samples")),),),
        (
            "/api/v1/doc/en-US/Web/CSS",
            (
                (
                    "documentData",
                    (
                        "locale",
                        "title",
                        "slug",
                        "tocHTML",
                        "bodyHTML",
                        "id",
                        "quickLinksHTML",
                        "parents",
                        "translations",
                        "wikiURL",
                        "summary",
                        "language",
                        "lastModified",
                        "absoluteURL",
                    ),
                ),
                "redirectURL",
            ),
        ),
    ],
    ids=("whoami", "doc"),
)
def test_api_basic(site_url, uri, expected_keys):
    """Basic test of site's api endpoints."""
    resp = request("get", site_url + uri)
    assert resp.status_code == 200
    assert resp.headers.get("content-type") == "application/json"
    data = resp.json()
    for item in expected_keys:
        if isinstance(item, tuple):
            key, sub_keys = item
        else:
            key, sub_keys = item, ()
        assert key in data
        for sub_key in sub_keys:
            assert sub_key in data[key]


@pytest.mark.headless
@pytest.mark.nondestructive
def test_api_doc_404(site_url):
    """Ensure that the beta site's doc api returns 404 for unknown docs."""
    url = site_url + "/api/v1/doc/en-US/NoSuchPage"
    resp = request("get", url)
    assert resp.status_code == 404


# Test value tuple is:
# - Expected locale prefix
# - Accept-Language header value
# - django-language cookie settings (False to omit)
# - ?lang param value (False to omit)
LOCALE_SELECTORS = {
    "en-US": ("en-US", "en-US", False, False),
    "es": ("es", "es", False, False),
    "fr-cookie": ("fr", "es", "fr", False),
    "de-param": ("de", "es", "fr", "de"),
}


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    "expected,accept,cookie,param",
    LOCALE_SELECTORS.values(),
    ids=list(LOCALE_SELECTORS),
)
@pytest.mark.parametrize(
    "slug",
    [
        "/search",
        "/events",
        "/profile",
        "/profiles/sheppy",
        "/users/signin",
        "/unsubscribe/1",
        "/promote",
        "/docs.json?slug=Web/HTML",
        "/docs/feeds/rss/l10n-updates",
        "/docs/feeds/atom/files",
        "/docs/feeds/rss/all",
        "/docs/feeds/rss/needs-review",
        "/docs/feeds/rss/needs-review/technical",
        "/docs/feeds/rss/revisions",
        "/docs/feeds/rss/tag/CSS" "/docs/localization-tag/inprogress",
        "/docs/all",
        "/docs/new?slug=test",
        "/docs/preview-wiki-content",
        "/docs/ckeditor_config.js",
        "/docs/needs-review/editorial",
        "/docs/tag/ARIA",
        "/docs/tags",
        "/docs/top-level",
        "/docs/with-errors",
        "/docs/without-parent",
        "/dashboards/spam",
        "/dashboards/macros",
        "/dashboards/revisions",
        "/dashboards/localization",
        "/dashboards/topic_lookup",
        "/dashboards/user_lookup",
        "/docs/Web/HTML",
        "/docs/Web/HTML$json",
        "/docs/Web/HTML$children",
        "/docs/Web/HTML$edit",
        "/docs/Web/HTML$move",
        "/docs/Web/HTML$files",
        "/docs/Web/HTML$purge",
        "/docs/Web/HTML$delete",
        "/docs/Web/HTML$history",
        "/docs/Web/HTML$translate",
        "/docs/Web/HTML$quick-review",
        "/docs/Web/HTML$subscribe",
        "/docs/Web/HTML$subscribe_to_tree",
        "/docs/Web/HTML$revision/1293895",
        "/docs/Web/HTML$repair_breadcrumbs",
        "/docs/Learn/CSS/Styling_text/Fundamentals$toc",
        "/docs/Learn/CSS/Styling_text/Fundamentals#Color",
        "/docs/Web/HTML$compare?locale=en-US&to=1299417&from=1293895",
        "/docs/Web/HTML$revert/1293895",
    ],
)
def test_locale_selection(site_url, slug, expected, accept, cookie, param):
    """
    Ensure that locale selection, which depends on the "lang" query
    parameter, the "django_language" cookie, and the "Accept-Language"
    header, works for the provided wiki URL's.
    """
    url = site_url + slug
    assert expected, "expected must be set to the expected locale prefix."
    assert accept, "accept must be set to the Accept-Langauge header value."

    request_kwargs = {
        "headers": {"X-Requested-With": "XMLHttpRequest", "Accept-Language": accept}
    }

    if cookie:
        request_kwargs["cookies"] = {"django_language": cookie}
    if param:
        request_kwargs["params"] = {"lang": param}

    response = request("get", url, **request_kwargs)
    assert response.status_code == 302
    assert response.headers["location"].startswith("/{}/".format(expected))


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize("locale", [None, "/de"])
@pytest.mark.parametrize("zone", ["Add-ons", "Apps", "Firefox", "Learn", "Marketplace"])
@pytest.mark.parametrize(
    "slug",
    [
        "{}/{}$edit",
        "{}/{}$move",
        "{}/{}$files",
        "{}/{}$purge",
        "{}/{}$delete",
        "{}/{}$translate",
        "{}/{}$quick-review",
        "{}/{}$revert/1284393",
        "{}/{}$subscribe",
        "{}/{}$subscribe_to_tree",
    ],
)
def test_former_vanity_302(wiki_site_url, slug, zone, locale):
    """Ensure that these former zone vanity URL's return 302."""
    locale = locale or ""
    url = wiki_site_url + slug.format(locale, zone)
    response = request("get", url)
    assert response.status_code == 302
    assert response.headers["location"].startswith("{}/docs/".format(locale))
    assert response.headers["location"].endswith(slug.format("", zone))


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    "slug",
    [
        "/en-US/dashboards/user_lookup?user=sheppy",
        "/en-US/dashboards/topic_lookup?topic=mathml",
    ],
)
def test_lookup_dashboards(wiki_site_url, slug):
    """Ensure that the topic and user dashboards require login."""
    response = request("get", wiki_site_url + slug)
    assert response.status_code == 302
    assert response.headers["location"].endswith("/users/signin?next=" + quote(slug))
