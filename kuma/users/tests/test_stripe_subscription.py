from datetime import datetime

import pytest

from django.conf import settings
from django.test import Client
from django.urls import reverse

from kuma.core.utils import safer_pyquery as pq
from kuma.users.models import User


@pytest.fixture
def payments_user(db, django_user_model):
    return User.objects.create(
        username='payments_user',
        email='payer@example.com',
        date_joined=datetime(2019, 1, 17, 15, 42))


def test_create_stripe_subscription(payments_user):
    if not settings.STRIPE_PLAN_ID:
        return

    client = Client()
    client.force_login(payments_user)
    data = {
        'stripe_token': 'tok_visa',
        'stripe_email': 'payer@example.com'
    }
    response = client.post(
        reverse('users.create_stripe_subscription'),
        data,
        follow=True,
        HTTP_HOST=settings.WIKI_HOST
    )
    page = pq(response.content)
    card_info = page('.card-info p').text()
    assert 'Visa ending in 4242' in card_info

    payments_user.refresh_from_db()
    assert len(payments_user.stripe_customer_id) > 0
