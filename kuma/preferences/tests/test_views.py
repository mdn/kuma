import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_preferences_index(client, settings):
    """Preferences landing page load successfully"""
    response = client.get(reverse("preferences_index"))
    assert response.status_code == 200
