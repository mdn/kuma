import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_accountsettings_index(client, settings):
    """AccountSettings landing page load successfully"""
    response = client.get(reverse("accountsettings_index"))
    assert response.status_code == 200
