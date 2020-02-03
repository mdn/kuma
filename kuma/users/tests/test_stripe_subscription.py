from datetime import datetime
from unittest.mock import patch

import pytest

from django.conf import settings
from django.test import Client
from django.urls import reverse

from kuma.core.utils import safer_pyquery as pq
from kuma.users.models import User


def mock_create_stripe_customer_and_subscription_for_user(user, email, stripe_token):
    pass


def mock_retrieve_stripe_subscription_info(user):
    return {
        'next_payment_at': '',
        'brand': 'MagicCard',
        'expires_at': '',
        'last4': 4242,
        'zip': 1337
    }


@pytest.fixture
def staff_user(db, django_user_model):
    return User.objects.create(
        username='staff_user',
        email='staff@example.com',
        date_joined=datetime(2019, 1, 17, 15, 42),
        is_staff=True
    )


@pytest.fixture
def normal_user(db, django_user_model):
    return User.objects.create(
        username='normal_user',
        email='user@example.com',
        date_joined=datetime(2019, 1, 17, 15, 42)
    )


@patch(
    "kuma.users.utils.create_stripe_customer_and_subscription_for_user",
    side_effect=mock_create_stripe_customer_and_subscription_for_user,
)
@patch(
    "kuma.users.utils.retrieve_stripe_subscription_info",
    side_effect=mock_retrieve_stripe_subscription_info
)
def test_create_stripe_subscription(mock1, mock2, staff_user):
    client = Client()
    client.force_login(staff_user)
    response = client.post(
        reverse('users.create_stripe_subscription'),
        data={
            'stripe_token': 'tok_visa',
            'stripe_email': 'payer@example.com'
        },
        follow=True,
        HTTP_HOST=settings.WIKI_HOST
    )
    page = pq(response.content)
    assert 'MagicCard ending in 4242' in page('.card-info p').text()


@patch(
    "kuma.users.utils.create_stripe_customer_and_subscription_for_user",
    side_effect=mock_create_stripe_customer_and_subscription_for_user,
)
@patch(
    "kuma.users.utils.retrieve_stripe_subscription_info",
    side_effect=mock_retrieve_stripe_subscription_info
)
def test_create_stripe_subscription_fail(mock1, mock2, normal_user):
    client = Client()
    client.force_login(normal_user)
    response = client.post(
        reverse('users.create_stripe_subscription'),
        data={
            'stripe_token': 'tok_visa',
            'stripe_email': 'payer@example.com'
        },
        follow=True,
        HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 403
