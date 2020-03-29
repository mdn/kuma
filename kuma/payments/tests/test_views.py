from dataclasses import dataclass
from unittest import mock
from unittest.mock import patch

import pytest
import stripe
from django.conf import settings
from waffle.testutils import override_flag

from kuma.core.tests import assert_no_cache_header, assert_redirect_to_wiki
from kuma.core.urlresolvers import reverse
from kuma.core.ga_tracking import (
    CATEGORY_MONTHLY_PAYMENTS,
    ACTION_FEEDBACK,
)


@dataclass
class MockSubscription:
    id: str = "sub_123456789"


@pytest.fixture
def stripe_user(wiki_user):
    wiki_user.stripe_customer_id = "fakeCustomerID123"
    wiki_user.save()
    return wiki_user


@pytest.mark.django_db
def test_payments_index(client):
    """Viewing the payments index page doesn't require you to be logged in"""
    response = client.get(reverse("payments_index"))
    assert response.status_code == 200


@patch("kuma.payments.views.track_event")
@pytest.mark.django_db
@override_flag("subscription", True)
def test_send_feedback(track_event_mock_signals, client, settings):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = True

    response = client.post(
        reverse("send_feedback"),
        content_type="application/json",
        data={"feedback": "my feedback"},
    )
    assert response.status_code == 204

    track_event_mock_signals.assert_called_with(
        CATEGORY_MONTHLY_PAYMENTS, ACTION_FEEDBACK, "my feedback",
    )


@pytest.mark.django_db
@override_flag("subscription", True)
@mock.patch("kuma.payments.views.get_stripe_customer_data", return_value=True)
def test_recurring_payment_management_no_customer_id(get, user_client):
    """The recurring payments page shows there are no active subscriptions."""
    response = user_client.get(
        reverse("recurring_payment_management"), HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert (
        '<button id="id_stripe_cancel_subscription"'
        ' name="stripe_cancel_subscription"'
    ) not in content
    assert "You have no active subscriptions." in content
    assert_no_cache_header(response)


@pytest.mark.django_db
@override_flag("subscription", True)
@mock.patch(
    "kuma.payments.views.get_stripe_customer_data",
    side_effect=stripe.error.InvalidRequestError(
        "No such customer: fakeCustomerID123",
        param="id",
        code="resourse_missing",
        http_status=404,
    ),
)
def test_recurring_payment_management_api_failure(get, stripe_user, user_client):
    """The page shows no active subscriptions if ID is unknown."""
    response = user_client.get(
        reverse("recurring_payment_management"), HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert (
        '<button id="id_stripe_cancel_subscription"'
        ' name="stripe_cancel_subscription"'
    ) not in content
    assert "You have no active subscriptions." in content
    assert_no_cache_header(response)


@pytest.mark.django_db
@override_flag("subscription", True)
@mock.patch(
    "kuma.payments.views.get_stripe_customer_data",
    return_value={
        "stripe_plan_amount": 64,
        "stripe_card_last4": 1234,
        "active_subscriptions": True,
    },
)
def test_recurring_payment_management_customer_id(get, user_client, stripe_user):
    """The recurring payments page shows there are active subscriptions."""
    response = user_client.get(
        reverse("recurring_payment_management"), HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert (
        '<button id="id_stripe_cancel_subscription"'
        ' name="stripe_cancel_subscription"'
    ) in content
    assert_no_cache_header(response)


@pytest.mark.django_db
@override_flag("subscription", True)
@mock.patch(
    "kuma.payments.views.cancel_stripe_customer_subscription",
    return_value=[MockSubscription().id],
)
@mock.patch(
    "kuma.payments.views.get_stripe_customer_data",
    return_value={
        "stripe_plan_amount": 0,
        "stripe_card_last4": 0,
        "active_subscriptions": False,
    },
)
def test_recurring_payment_management_cancel(_cancel, get, user_client, stripe_user):
    """A subscription can be cancelled from the recurring payments page."""
    response = user_client.post(
        reverse("recurring_payment_management"),
        data={"stripe_cancel_subscription": ""},
        HTTP_HOST=settings.WIKI_HOST,
    )
    assert response.status_code == 200
    assert get.called
    text = "Your monthly subscription has been successfully canceled"
    content = response.content.decode(response.charset)
    assert text in content


@pytest.mark.django_db
@override_flag("subscription", True)
@mock.patch(
    "kuma.payments.views.cancel_stripe_customer_subscription",
    side_effect=stripe.error.InvalidRequestError(
        "No such customer: fakeCustomerID123",
        param="id",
        code="resourse_missing",
        http_status=404,
    ),
)
@mock.patch(
    "kuma.payments.views.get_stripe_customer_data",
    return_value={
        "stripe_plan_amount": 64,
        "stripe_card_last4": "1234",
        "active_subscriptions": True,
    },
)
def test_recurring_payment_management_cancel_fails(
    _cancel, get, user_client, stripe_user
):
    """A message is displayed if cancelling fails due to unknow customer."""
    response = user_client.post(
        reverse("recurring_payment_management"),
        data={"stripe_cancel_subscription": ""},
        HTTP_HOST=settings.WIKI_HOST,
    )
    assert response.status_code == 200
    assert get.called
    text = "There was a problem canceling your subscription"
    content = response.content.decode(response.charset)
    assert text in content


@pytest.mark.django_db
@override_flag("subscription", True)
@mock.patch(
    "kuma.payments.views.cancel_stripe_customer_subscription", return_value=True
)
@mock.patch("kuma.payments.views.get_stripe_customer_data", return_value=True)
def test_recurring_payment_management_not_logged_in(get, cancel_, client):
    """The recurring payments form succeeds with a valid Stripe token."""
    response = client.get(
        reverse("recurring_payment_management"), HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 302
    assert response.url == "?next=".join(
        [reverse("account_login"), reverse("recurring_payment_management")]
    )


@override_flag("subscription", True)
@pytest.mark.parametrize(
    "endpoint", ["recurring_payment_management"],
)
def test_redirect(db, client, endpoint):
    """Redirect to the wiki domain if not already."""
    url = reverse(endpoint)
    response = client.get(url)
    assert_redirect_to_wiki(response, url)
