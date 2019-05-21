from __future__ import unicode_literals

import mock
import pytest
import stripe

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse


@pytest.fixture
def stripe_user(wiki_user):
    wiki_user.stripe_customer_id = 'fakeCustomerID123'
    wiki_user.save()
    return wiki_user


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_payments_view(mock_enabled, client, settings):
    """The one-time payment page renders."""
    response = client.get(reverse('payments'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_payment_terms_view(mock_enabled, client, settings):
    """The payment terms page renders."""
    response = client.get(reverse('payment_terms'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
@mock.patch('kuma.payments.views.get_stripe_customer_data', return_value=True)
def test_recurring_payment_management_no_customer_id(enabled_, get, user_client):
    """The recurring payments page shows there are no active subscriptions."""
    response = user_client.get(reverse('recurring_payment_management'))
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert ('<button id="id_stripe_cancel_subscription"'
            ' name="stripe_cancel_subscription"') not in content
    assert "You have no active subscriptions." in content
    assert_no_cache_header(response)


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
@mock.patch('kuma.payments.views.get_stripe_customer_data',
            side_effect=stripe.error.InvalidRequestError(
                'No such customer: fakeCustomerID123',
                param='id',
                code='resourse_missing',
                http_status=404))
def test_recurring_payment_management_api_failure(enabled_, get, stripe_user, user_client):
    """The page shows no active subscriptions if ID is unknown."""
    response = user_client.get(reverse('recurring_payment_management'))
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert ('<button id="id_stripe_cancel_subscription"'
            ' name="stripe_cancel_subscription"') not in content
    assert "You have no active subscriptions." in content
    assert_no_cache_header(response)


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
@mock.patch('kuma.payments.views.get_stripe_customer_data', return_value={
    'stripe_plan_amount': 64,
    'stripe_card_last4': 1234,
    'active_subscriptions': True
})
def test_recurring_payment_management_customer_id(enabled_, get, user_client, stripe_user):
    """The recurring payments page shows there are active subscriptions."""
    response = user_client.get(reverse('recurring_payment_management'))
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert ('<button id="id_stripe_cancel_subscription"'
            ' name="stripe_cancel_subscription"') in content
    assert_no_cache_header(response)


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
@mock.patch('kuma.payments.views.cancel_stripe_customer_subscription', return_value=True)
@mock.patch('kuma.payments.views.get_stripe_customer_data', return_value={
    'stripe_plan_amount': 0,
    'stripe_card_last4': 0,
    'active_subscriptions': False
})
def test_recurring_payment_management_cancel(enabled_, get, cancel_, user_client, stripe_user):
    """A subscription can be cancelled from the recurring payments page."""
    response = user_client.post(
        reverse('recurring_payment_management'),
        data={'stripe_cancel_subscription': ''}
    )
    assert response.status_code == 200
    assert cancel_.called
    assert get.called
    text = 'Your monthly subscription has been successfully canceled'
    content = response.content.decode(response.charset)
    assert text in content


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
@mock.patch('kuma.payments.views.cancel_stripe_customer_subscription',
            side_effect=stripe.error.InvalidRequestError(
                'No such customer: fakeCustomerID123',
                param='id',
                code='resourse_missing',
                http_status=404))
@mock.patch('kuma.payments.views.get_stripe_customer_data', return_value={
    'stripe_plan_amount': 64,
    'stripe_card_last4': '1234',
    'active_subscriptions': True
})
def test_recurring_payment_management_cancel_fails(enabled_, get, cancel_, user_client, stripe_user):
    """A message is displayed if cancelling fails due to unknow customer."""
    response = user_client.post(
        reverse('recurring_payment_management'),
        data={'stripe_cancel_subscription': ''}
    )
    assert response.status_code == 200
    assert cancel_.called
    assert get.called
    text = 'There was a problem canceling your subscription'
    content = response.content.decode(response.charset)
    assert text in content


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
@mock.patch('kuma.payments.views.cancel_stripe_customer_subscription', return_value=True)
@mock.patch('kuma.payments.views.get_stripe_customer_data', return_value=True)
def test_recurring_payment_management_not_logged_in(enabled_, get, cancel_, client):
    """The recurring payments form succeeds with a valid Stripe token."""
    response = client.get(reverse('recurring_payment_management'))
    assert response.status_code == 302
    assert response.url == '?next='.join([reverse('account_login'), reverse('recurring_payment_management')])
