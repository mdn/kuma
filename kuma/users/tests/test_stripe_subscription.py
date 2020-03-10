from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from django.conf import settings
from django.core import mail
from django.test import Client
from django.urls import reverse
from waffle.testutils import override_flag

from kuma.core.utils import safer_pyquery as pq
from kuma.users.models import User


from . import user


def mock_retrieve_stripe_subscription_info(user):
    return {
        "next_payment_at": "",
        "brand": "MagicCard",
        "expires_at": "",
        "last4": 4242,
        "zip": 1337,
    }


@pytest.fixture
def test_user(db, django_user_model):
    return User.objects.create(
        username="test_user",
        email="staff@example.com",
        date_joined=datetime(2019, 1, 17, 15, 42),
    )


@patch("kuma.users.views.create_stripe_customer_and_subscription_for_user")
@patch(
    "kuma.users.views.retrieve_stripe_subscription_info",
    side_effect=mock_retrieve_stripe_subscription_info,
)
@override_flag("subscription", True)
def test_create_stripe_subscription(mock1, mock2, test_user):
    client = Client()
    client.force_login(test_user)

    response = client.post(
        reverse("users.create_stripe_subscription"),
        data={"stripe_token": "tok_visa", "stripe_email": "payer@example.com"},
        follow=True,
        HTTP_HOST=settings.WIKI_HOST,
    )

    assert response.status_code == 200

    page = pq(response.content)
    assert page(".stripe-error").size() == 0
    assert "MagicCard ending in 4242" in page(".card-info p").text()


@patch("kuma.users.stripe_utils.create_stripe_customer_and_subscription_for_user")
@patch(
    "kuma.users.stripe_utils.retrieve_stripe_subscription_info",
    side_effect=mock_retrieve_stripe_subscription_info,
)
@override_flag("subscription", False)
def test_create_stripe_subscription_fail(mock1, mock2, test_user):
    client = Client()
    client.force_login(test_user)
    response = client.post(
        reverse("users.create_stripe_subscription"),
        data={"stripe_token": "tok_visa", "stripe_email": "payer@example.com"},
        follow=True,
        HTTP_HOST=settings.WIKI_HOST,
    )
    assert response.status_code == 403


def mock_stripe_payment_event(payload, api_key):
    return SimpleNamespace(
        **{
            "type": "invoice.payment_succeeded",
            "data": SimpleNamespace(
                **{
                    "object": SimpleNamespace(
                        **{
                            "customer": "cus_mock_testuser",
                            "created": 1583842724,
                            "invoice_pdf": "https://developer.mozilla.org/mock-invoice-pdf-url",
                        }
                    )
                }
            ),
        }
    )


@patch(
    "stripe.Event.construct_from", side_effect=mock_stripe_payment_event,
)
@pytest.mark.django_db
def test_stripe_payment_succeeded_sends_invoice_mail(mock1, client):
    testuser = user(
        save=True,
        username="testuser",
        email="testuser@example.com",
        stripe_customer_id="cus_mock_testuser",
    )
    client.post(
        reverse("users.stripe_payment_succeeded_hook"),
        content_type="application/json",
        data={},
    )
    assert len(mail.outbox) == 1
    payment_email = mail.outbox[0]
    assert payment_email.to == [testuser.email]
    print(payment_email.body)
    assert "manage monthly subscriptions" in payment_email.body
    assert "invoice" in payment_email.subject
