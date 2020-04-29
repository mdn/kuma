from dataclasses import dataclass

import pytest
from django.conf import settings
from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse


@dataclass
class MockSubscription:
    id: str = "sub_123456789"


@pytest.mark.django_db
def test_payments_index(client):
    """Viewing the payments index page doesn't require you to be logged in.
    Payments page shows support email and header."""
    response = client.get(reverse("payments_index"))
    assert response.status_code == 200
    doc = pq(response.content)
    assert settings.CONTRIBUTION_SUPPORT_EMAIL in doc.find(".contributions-page").text()
    assert doc.find("h1").text() == "Become a monthly supporter"
    assert doc(".subscriptions h2").text() == "You will be MDN member number 1"


@pytest.mark.django_db
def test_payments_url_fixes(client):
    """These tests just make sure that the use of trailing slashes are correct."""
    url = reverse("payments_index")
    # if you remove the trailing / it should redirect back to that
    assert url.endswith("/")
    response = client.get(url[:-1], follow=False)
    assert response.status_code == 301
    assert response["location"] == url
    response = client.get(url + "xxxx", follow=False)
    assert response.status_code == 404
