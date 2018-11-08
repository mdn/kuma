import mock
import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from django.test.utils import override_settings


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_contribute_view(mock_enabled, client, settings):
    """If enabled, contribution page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('payments'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_payment_terms_view(mock_enabled, client, settings):
    """If enabled, contribution page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('payment_terms'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_thanks_view(mock_enabled, client, settings):
    """If enabled, contribution thank you page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('payment_succeeded'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_error_view(mock_enabled, client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('payment_error'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('view', ('payments',
                                  'payment_succeeded',
                                  'payment_error',
                                  'recurring_payment_initial',
                                  'recurring_payment_subscription'))
@mock.patch('kuma.payments.views.enabled')
def test_views_404(mock_enabled, view, client, settings):
    """If disabled, contribution pages are 404."""
    mock_enabled.return_value = False
    response = client.get(reverse(view))
    assert response.status_code == 404


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_error_recurring_payment_initial_view(mock_enabled, client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('recurring_payment_initial'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_login_required_recurring_payment_subscription_view_redirect(mock_enabled, client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('recurring_payment_subscription'))
    assert response.status_code == 302


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_login_required_recurring_payment_subscription_view_ok(mock_enabled, user_client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
    response = user_client.get(reverse('recurring_payment_subscription'))
    assert_no_cache_header(response)
    assert response.status_code == 200


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_post_method_redirect_recurring_payment_subscription(mock_enabled, user_client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
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
@mock.patch('kuma.payments.views.enabled')
@mock.patch('kuma.payments.views.RecurringPaymentForm.make_recurring_payment_charge', return_value=True)
def test_post_method_recurring_payment_subscription(mock_enabled, form, user_client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
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
@mock.patch('kuma.payments.views.enabled')
def test_template_render_logged_in_recurring_payment_initial_view(mock_enabled, user_client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
    response = user_client.get(reverse('recurring_payment_initial'))
    assert_no_cache_header(response)
    assert response.status_code == 200
    assert '<input type="hidden"' in response.content
    assert 'id="id_stripe_token"' in response.content
    assert 'id="stripe_source_setup"' in response.content
    assert 'id="id_stripe_public_key"' in response.content
    assert '<form id="contribute-form"' in response.content
    assert '<input type="email"' in response.content
    assert 'id="id_donation_amount"' in response.content
    assert 'id="id_donation_choices"' in response.content
    assert 'id="id_accept_checkbox"' in response.content


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_template_render_not_logged_in_recurring_payment_initial_view(mock_enabled, client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('recurring_payment_initial'))
    assert_no_cache_header(response)
    assert response.status_code == 200
    assert '<input type="hidden"' in response.content
    assert 'id="id_stripe_token"' not in response.content
    assert 'id="stripe_source_setup"' in response.content
    assert 'id="id_stripe_public_key"' not in response.content
    assert '<form id="contribute-form"' in response.content
    assert '<input type="email"' in response.content
    assert 'id="id_donation_amount"' in response.content
    assert 'id="id_donation_choices"' in response.content


@pytest.mark.django_db
@mock.patch('kuma.payments.views.enabled')
def test_template_render_not_logged_in_payment_view(mock_enabled, client, settings):
    """If enabled, contribution error page is returned."""
    mock_enabled.return_value = True
    response = client.get(reverse('payments'))
    assert_no_cache_header(response)
    assert response.status_code == 200
    assert '<input type="hidden"' in response.content
    assert 'id="id_stripe_token"' in response.content
    assert 'id="id_stripe_public_key"' in response.content
    assert '<form id="contribute-form"' in response.content
    assert '<input type="email"' in response.content
    assert 'id="id_donation_amount"' in response.content
    assert 'id="id_donation_choices"' in response.content
    assert 'id="id_accept_checkbox"' not in response.content
