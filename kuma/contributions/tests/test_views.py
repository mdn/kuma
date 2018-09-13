import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_contribute_view(client):
    response = client.get(reverse('contribute'))
    assert response.status_code == 200
