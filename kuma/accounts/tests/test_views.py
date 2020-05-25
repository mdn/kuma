import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_account_index(client, settings):
    """Account landing page requires login"""
    response = client.get(reverse("account_index"))
    assert response.status_code == 302
    assert reverse("account_login") in response["Location"]
