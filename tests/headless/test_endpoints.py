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
