from urlparse import urlsplit
import re

import pytest
import requests

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
