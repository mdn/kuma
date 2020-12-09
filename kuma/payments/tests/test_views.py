import pytest
from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_payments_index(client, settings):
    """Viewing the payments index page doesn't require you to be logged in.
    Payments page shows support email and header."""
    response = client.get(reverse("payments_index"))
    assert response.status_code == 200
    doc = pq(response.content)
    assert settings.CONTRIBUTION_SUPPORT_EMAIL in doc.find(".contributions-page").text()
    assert doc.find("h1").text() == "Become a monthly supporter"
    assert doc(".subscriptions h2").text() == "You will be MDN member number 1"


@pytest.mark.django_db
def test_payments_index_disabled(client, settings):
    """Viewing the payments index page doesn't require you to be logged in.
    Payments page shows support email and header."""
    settings.ENABLE_SUBSCRIPTIONS = False
    response = client.get(reverse("payments_index"))
    assert response.status_code == 404


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


def test_payments_recurring_management_redirect(client):
    """That old redirect used to be something we exposed, so it's important to
    assert that we took care of redirecting it to its new location."""
    response = client.get(reverse("recurring_payment_management"), follow=False)
    assert response.status_code == 301
    assert response["location"] == reverse("payment_management")
