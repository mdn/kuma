import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_contribute_view(client):
    response = client.get(reverse('contribute'))
    assert_no_cache_header(response)
    assert response.status_code == 200
