import re
from urlparse import urlsplit

import pytest
import requests
from pyquery import PyQuery


from . import INDEXED_WEB_DOMAINS


META_ROBOTS_RE = re.compile(r'''(?x)    # Verbose regex mode
    <meta\s+                        # meta tag followed by whitespace
    name="robots"\s*                # name=robots
    content="(?P<content>[^"]+)"    # capture the content
    \s*>                            # end meta tag
''')


@pytest.fixture()
def is_indexed(base_url):
    hostname = urlsplit(base_url).netloc
    return hostname in INDEXED_WEB_DOMAINS


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document_json(base_url):
    url = base_url + '/en-US/docs/Web$json'
    resp = requests.get(url)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'application/json'
    assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document(base_url, is_indexed):
    url = base_url + '/en-US/docs/Web'
    resp = requests.get(url)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/html; charset=utf-8'
    meta = META_ROBOTS_RE.search(resp.content)
    assert meta
    content = meta.group('content')
    if is_indexed:
        assert content == 'index, follow'
    else:
        assert content == 'noindex, nofollow'


@pytest.mark.headless
@pytest.mark.nondestructive
def test_user_document(base_url):
    url = base_url + '/en-US/docs/User:anonymous:uitest'
    resp = requests.get(url)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/html; charset=utf-8'
    meta = META_ROBOTS_RE.search(resp.content)
    assert meta
    content = meta.group('content')
    # Pages with legacy MindTouch namespaces like 'User:' never get
    # indexed, regardless of what the base url is
    assert content == 'noindex, nofollow'


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document_based_redirection(base_url):
    """Ensure that content-based redirects properly redirect."""
    url = base_url + '/en-US/docs/MDN/Promote'
    resp = requests.get(url)
    assert resp.status_code == 200
    assert len(resp.history) == 1
    assert resp.history[0].status_code == 301
    assert resp.url == base_url + '/en-US/docs/MDN/About/Promote'


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document_based_redirection_suppression(base_url):
    """
    Ensure that the redirect directive and not the content of the target
    page is displayed when content-based redirects are suppressed.
    """
    url = base_url + '/en-US/docs/MDN/Promote?redirect=no'
    resp = requests.get(url)
    assert resp.status_code == 200
    assert not resp.history
    body = PyQuery(resp.text)('#wikiArticle')
    assert body.text().startswith('REDIRECT ')
    assert body.find('a[href="/en-US/docs/MDN/About/Promote"]')


@pytest.mark.smoke
@pytest.mark.headless
@pytest.mark.nondestructive
def test_home(base_url, is_indexed):
    url = base_url + '/en-US/'
    resp = requests.get(url)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/html; charset=utf-8'
    meta = META_ROBOTS_RE.search(resp.content)
    assert meta
    content = meta.group('content')
    if is_indexed:
        assert content == 'index, follow'
    else:
        assert content == 'noindex, nofollow'


@pytest.mark.headless
@pytest.mark.nondestructive
def test_hreflang_basic(base_url):
    """Ensure that we're specifying the correct value for lang and hreflang."""
    url = base_url + '/en-US/docs/Web/HTTP'
    resp = requests.get(url)
    assert resp.status_code == 200
    html = PyQuery(resp.text)
    assert html.attr('lang') == 'en'
    assert html.find('head > link[hreflang="en"][href="{}"]'.format(url))


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('uri', ['/api/v1/whoami', '/api/v1/doc/en-US/Web/CSS'])
def test_beta_endpoints_not_on_wiki(wiki_site_url, uri):
    """Ensure that these beta endpoints are not provided by the wiki site."""
    resp = requests.get(wiki_site_url + uri)
    assert resp.status_code == 404


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'uri,expected_keys',
    [('/api/v1/whoami', ('username', 'is_staff', 'is_authenticated', 'timezone',
                         'is_beta_tester', 'gravatar_url', 'is_superuser')),
     ('/api/v1/doc/en-US/Web/CSS', ('locale', 'title', 'slug', 'tocHTML',
                                    'bodyHTML', 'id', 'quickLinksHTML',
                                    'parents', 'translations', 'editURL',
                                    'summary', 'language', 'absoluteURL',
                                    'redirectURL'))],
    ids=('whomai', 'doc')
)
def test_beta_api_basic(beta_site_url, uri, expected_keys):
    """Basic test of beta site's api endpoints."""
    resp = requests.get(beta_site_url + uri)
    assert resp.status_code == 200
    assert resp.headers.get('content-type') == 'application/json'
    data = resp.json()
    for key in expected_keys:
        assert key in data


@pytest.mark.headless
@pytest.mark.nondestructive
def test_api_doc_404(beta_site_url):
    """Ensure that the beta site's doc api returns 404 for unknown docs."""
    url = beta_site_url + '/api/v1/doc/en-US/NoSuchPage'
    resp = requests.get(url)
    assert resp.status_code == 404
