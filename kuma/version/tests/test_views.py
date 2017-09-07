import os
from urlparse import urljoin

import pytest
import requests_mock

from kuma.core.urlresolvers import reverse
from kuma.wiki.constants import KUMASCRIPT_BASE_URL


@pytest.mark.parametrize('method', ['get', 'head'])
def test_revision_hash(client, db, method):
    response = getattr(client, method)(reverse('version.kuma'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain; charset=utf-8'
    if method == 'get':
        assert response.content == os.getenv('REVISION_HASH', 'undefined')


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_revision_hash_405s(client, db, method):
    response = getattr(client, method)(reverse('version.kuma'))
    assert response.status_code == 405


@pytest.mark.parametrize('method', ['get', 'head'])
def test_kumascript_revision_hash(client, db, method):
    hash = '8da6b8f41ce8eb425f669fc17e3edcd48705fa46'
    ks_revision_url = urljoin(KUMASCRIPT_BASE_URL, 'revision/')
    with requests_mock.mock() as mock_requests:
        mock_requests.get(
            ks_revision_url,
            text=hash,
            headers={'content-type': 'text/plain; charset=utf-8'}
        )
        response = client.get(reverse('version.kumascript'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain; charset=utf-8'
    if method == 'get':
        assert response.content == hash


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_kumascript_revision_hash_405s(client, db, method):
    response = getattr(client, method)(reverse('version.kumascript'))
    assert response.status_code == 405
