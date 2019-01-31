from __future__ import unicode_literals

import mock
import pytest
import stripe

from django.test.utils import override_settings

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
def test_thanks_view(mock_enabled, client, settings):
    """The thank you page renders."""
    response = client.get(reverse('payment_succeeded'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_error_view(mock_enabled, client, settings):
    """The error page renders."""
    response = client.get(reverse('payment_error'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('view', ('payments',
                                  'payment_succeeded',
                                  'payment_error',
                                  'recurring_payment_initial',
                                  'recurring_payment_subscription'))
@mock.patch('kuma.payments.views.enabled', return_value=False)
def test_views_404(mock_enabled, view, client, settings):
    """If disabled, payment pages are 404."""
    response = client.get(reverse(view))
    assert response.status_code == 404


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_error_recurring_payment_initial_view(mock_enabled, client, settings):
    """The initial recurring payments page renders."""
    response = client.get(reverse('recurring_payment_initial'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_login_required_recurring_payment_subscription_view_redirect(mock_enabled, client, settings):
    """The recurring payments page redirects anon users."""
    response = client.get(reverse('recurring_payment_subscription'))
    assert response.status_code == 302


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_login_required_recurring_payment_subscription_view_ok(mock_enabled, user_client, settings):
    """The recurring payments subscription page renders for logged-in users."""
    response = user_client.get(reverse('recurring_payment_subscription'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_post_method_redirect_recurring_payment_subscription(mock_enabled, user_client, settings):
    """The recurring payments form errors without a Stripe token."""
    response = user_client.post(
        reverse('recurring_payment_subscription'),
        data={
            'name': 'True name',
            'email': 'true.email@mozilla.com',
            'donation_amount': 124,
            'accept_checkbox': True
        }
    )
    assert_no_cache_header(response)
    assert response.status_code == 302
    assert response.url == reverse('recurring_payment_error')


@override_settings(MDN_CONTRIBUTION_CONFIRMATION_EMAIL=False)
@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
@mock.patch('kuma.payments.views.RecurringPaymentForm.make_recurring_payment_charge', return_value=True)
def test_post_method_recurring_payment_subscription(mock_enabled, form, user_client, settings):
    """The recurring payments form succeeds with a valid Stripe token."""
    response = user_client.post(
        reverse('recurring_payment_subscription'),
        data={
            'name': 'True name',
            'email': 'true.email@mozilla.com',
            'donation_amount': 63,
            'accept_checkbox': True,
            'stripe_token': 'some-token',
            'stripe_public_key': 'some-public-key',
        }
    )
    assert_no_cache_header(response)
    assert response.status_code == 302
    assert response.url == reverse('recurring_payment_succeeded')


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_template_render_logged_in_recurring_payment_initial_view(mock_enabled, user_client, settings):
    """Logged-in users get the full recurring payments form."""
    response = user_client.get(reverse('recurring_payment_initial'))
    assert_no_cache_header(response)
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert '<input type="hidden"' in content
    assert 'id="id_stripe_token"' in content
    assert 'id="stripe_source_setup"' in content
    assert 'id="id_stripe_public_key"' in content
    assert '<form id="contribute-form"' in content
    assert '<input type="email"' in content
    assert 'id="id_donation_amount"' in content
    assert 'id="id_donation_choices"' in content
    assert 'id="id_accept_checkbox"' in content


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_template_render_not_logged_in_recurring_payment_initial_view(mock_enabled, client, settings):
    """Anonymous users get a provisionary recurring payments form."""
    response = client.get(reverse('recurring_payment_initial'))
    assert_no_cache_header(response)
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert '<input type="hidden"' in content
    assert 'id="id_stripe_token"' not in content
    assert 'id="stripe_source_setup"' in content
    assert 'id="id_stripe_public_key"' not in content
    assert '<form id="contribute-form"' in content
    assert '<input type="email"' in content
    assert 'id="id_donation_amount"' in content
    assert 'id="id_donation_choices"' in content


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled', return_value=True)
def test_template_render_not_logged_in_payment_view(mock_enabled, client, settings):
    """Anonymous users get the full one-time payments form."""
    response = client.get(reverse('payments'))
    assert_no_cache_header(response)
    assert response.status_code == 200
    content = response.content.decode(response.charset)
    assert '<input type="hidden"' in content
    assert 'id="id_stripe_token"' in content
    assert 'id="id_stripe_public_key"' in content
    assert '<form id="contribute-form"' in content
    assert '<input type="email"' in content
    assert 'id="id_donation_amount"' in content
    assert 'id="id_donation_choices"' in content
    assert 'id="id_accept_checkbox"' in content


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
    assert response.status_code == 200


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
    assert response.status_code == 200


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
