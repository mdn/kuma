from types import SimpleNamespace
from unittest import mock

import pytest
from stripe.error import APIError
from waffle.testutils import override_flag

from kuma.core.ga_tracking import (
    ACTION_SUBSCRIPTION_CANCELED,
    CATEGORY_MONTHLY_PAYMENTS,
)
from kuma.core.urlresolvers import reverse
from kuma.users.models import UserSubscription
from kuma.users.tests import create_user


@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_subscription_created(mock1, client):
    mock1.return_value = SimpleNamespace(
        type="customer.subscription.created",
        data=SimpleNamespace(
            object=SimpleNamespace(customer="cus_mock_testuser", id="sub_123456789")
        ),
    )

    testuser = create_user(
        save=True,
        username="testuser",
        email="testuser@example.com",
        stripe_customer_id="cus_mock_testuser",
    )
    UserSubscription.set_active(testuser, "sub_123456789")
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 200
    (user_subscription,) = UserSubscription.objects.filter(user=testuser)
    assert not user_subscription.canceled


@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_subscription_canceled(mock1, client):
    mock1.return_value = SimpleNamespace(
        type="customer.subscription.deleted",
        data=SimpleNamespace(
            object=SimpleNamespace(customer="cus_mock_testuser", id="sub_123456789")
        ),
    )

    testuser = create_user(
        save=True,
        username="testuser",
        email="testuser@example.com",
        stripe_customer_id="cus_mock_testuser",
    )
    UserSubscription.set_active(testuser, "sub_123456789")
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 200
    (user_subscription,) = UserSubscription.objects.filter(user=testuser)
    assert user_subscription.canceled


@pytest.mark.django_db
def test_stripe_hook_invalid_json(client):
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data="{not valid!",
    )
    assert response.status_code == 400


@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_hook_unexpected_type(mock1, client):
    mock1.return_value = SimpleNamespace(
        type="not.expected",
        data=SimpleNamespace(foo="bar"),
    )
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 400


@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_hook_stripe_api_error(mock1, client):
    mock1.side_effect = APIError("badness")
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 400


@mock.patch("kuma.api.v1.subscription.track_event")
@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_subscription_canceled_sends_ga_tracking(
    mock1, track_event_mock_signals, client
):
    mock1.return_value = SimpleNamespace(
        type="customer.subscription.deleted",
        data=SimpleNamespace(
            object=SimpleNamespace(customer="cus_mock_testuser", id="sub_123456789")
        ),
    )

    create_user(
        save=True,
        username="testuser",
        email="testuser@example.com",
        stripe_customer_id="cus_mock_testuser",
    )
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 200

    track_event_mock_signals.assert_called_with(
        CATEGORY_MONTHLY_PAYMENTS, ACTION_SUBSCRIPTION_CANCELED, "webhook"
    )


@mock.patch("stripe.Price.retrieve")
def test_subscription_config(mock_retrieve, client, settings):
    def mocked_get_price(id):
        assert id in settings.STRIPE_PRICE_IDS
        if settings.STRIPE_PRICE_IDS.index(id) == 1:
            return SimpleNamespace(
                unit_amount=555 * 10,
                currency="sek",
                id=id,
            )
        else:
            return SimpleNamespace(
                unit_amount=555,
                currency="sek",
                id=id,
            )

    mock_retrieve.side_effect = mocked_get_price
    url = reverse("api.v1.subscriptions.config")
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["public_key"] == settings.STRIPE_PUBLIC_KEY
    assert response.json()["prices"] == [
        {"currency": "sek", "unit_amount": 555, "id": settings.STRIPE_PRICE_IDS[0]},
        {
            "currency": "sek",
            "unit_amount": 555 * 10,
            "id": settings.STRIPE_PRICE_IDS[1],
        },
    ]


@mock.patch("stripe.billing_portal.Session.create")
def test_subscription_customer_portal(mock_create, user_client, wiki_user):

    fake_session_url = "https://stripe.example/123456789"

    def mocked_create_session(customer, return_url):
        return SimpleNamespace(url=fake_session_url)

    mock_create.side_effect = mocked_create_session
    url = reverse("api.v1.subscriptions.customer_portal")
    response = user_client.get(url)
    assert response.status_code == 405
    response = user_client.post(url)
    assert response.status_code == 403
    assert "subscription is not enabled" in response.content.decode()

    with override_flag("subscription", active=True):
        response = user_client.post(url)
        assert response.status_code == 403
        assert "no existing stripe_customer_id" in response.content.decode()

        wiki_user.stripe_customer_id = "abc123"
        wiki_user.save()
        response = user_client.post(url)
        assert response.status_code == 200
        assert response.json()["url"] == fake_session_url


def test_subscription_customer_portal_anonymous(client):
    url = reverse("api.v1.subscriptions.customer_portal")
    response = client.post(url)
    assert response.status_code == 403
    assert "user not authenticated" in response.content.decode()


@mock.patch("stripe.checkout.Session.create")
@mock.patch("stripe.Customer.create")
def test_subscription_checkout_auth(
    mock_create_customer, mock_create_session, user_client
):

    fake_session_id = "xyz123456789"

    def mocked_create_session(*args, **kwargs):
        return SimpleNamespace(id=fake_session_id)

    mock_create_session.side_effect = mocked_create_session

    fake_customer_id = "abc123"

    def mocked_create_customer(email):
        return {"id": fake_customer_id}

    mock_create_customer.side_effect = mocked_create_customer

    url = reverse("api.v1.subscriptions.checkout")
    response = user_client.get(url)
    assert response.status_code == 405
    response = user_client.post(url)
    assert response.status_code == 403
    assert "subscription is not enabled" in response.content.decode()

    with override_flag("subscription", active=True):
        response = user_client.post(url)
        assert response.status_code == 200
        assert response.json()["sessionId"] == fake_session_id


def test_subscription_checkout_anonymous(client):
    url = reverse("api.v1.subscriptions.checkout")
    response = client.post(url)
    assert response.status_code == 403
    assert "user not authenticated" in response.content.decode()
