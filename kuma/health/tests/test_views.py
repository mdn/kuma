import pytest
from django.core.urlresolvers import reverse


@pytest.mark.parametrize('http_method',
                         ['get', 'head', 'put', 'post', 'delete', 'options'])
@pytest.mark.parametrize('endpoint', ['health.liveness', 'health.readiness'])
def test_basic_health(db, client, http_method, endpoint):
    url = reverse(endpoint)
    response = getattr(client, http_method)(url)
    assert (response.status_code ==
            204 if http_method in ('get', 'head') else 405)
