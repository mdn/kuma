from urllib.parse import urljoin

import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.wiki.constants import KUMASCRIPT_BASE_URL


@pytest.mark.parametrize('method', ['get', 'head'])
def test_revision_hash(client, db, method, settings):
    settings.REVISION_HASH = 'the_revision_hash'
    response = getattr(client, method)(reverse('version.kuma'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain; charset=utf-8'
    assert_no_cache_header(response)
    if method == 'get':
        assert response.content.decode('utf-8') == 'the_revision_hash'


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_revision_hash_405s(client, db, method):
    response = getattr(client, method)(reverse('version.kuma'))
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.parametrize('method', ['get', 'head'])
def test_kumascript_revision_hash(client, db, method, mock_requests):
    hash = '8da6b8f41ce8eb425f669fc17e3edcd48705fa46'
    ks_revision_url = urljoin(KUMASCRIPT_BASE_URL, 'revision/')
    mock_requests.get(
        ks_revision_url,
        text=hash,
        headers={'content-type': 'text/plain; charset=utf-8'}
    )
    response = client.get(reverse('version.kumascript'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain; charset=utf-8'
    assert_no_cache_header(response)
    if method == 'get':
        assert response.content.decode('utf-8') == hash


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_kumascript_revision_hash_405s(client, db, method):
    response = getattr(client, method)(reverse('version.kumascript'))
    assert response.status_code == 405
    assert_no_cache_header(response)
