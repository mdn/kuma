import mock
import pytest
from django.db import DatabaseError
from django.core.urlresolvers import reverse


@pytest.mark.parametrize('http_method',
                         ['get', 'head', 'put', 'post', 'delete', 'options'])
def test_liveness(db, client, http_method):
    url = reverse('health.liveness')
    response = getattr(client, http_method)(url)
    assert (response.status_code ==
            204 if http_method in ('get', 'head') else 405)


@pytest.mark.parametrize('http_method',
                         ['get', 'head', 'put', 'post', 'delete', 'options'])
def test_readiness(db, client, http_method):
    url = reverse('health.readiness')
    response = getattr(client, http_method)(url)
    assert (response.status_code ==
            204 if http_method in ('get', 'head') else 405)


def test_readiness_with_db_error(db, client):
    url = reverse('health.readiness')
    with mock.patch('kuma.wiki.models.Document.objects') as mock_manager:
        mock_manager.filter.side_effect = DatabaseError('fubar')
        response = client.get(url)
    assert response.status_code == 503
    assert 'fubar' in response.reason_phrase
