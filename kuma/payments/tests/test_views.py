import mock
import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase

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


class RecurringPaymentTests(UserTestCase):

    @pytest.mark.django_db
    @mock.patch('kuma.payments.views.enabled')
    def test_error_recurring_payment_initial_view(self, mock_enabled):
        """If enabled, contribution error page is returned."""
        mock_enabled.return_value = True
        response = self.client.get(reverse('recurring_payment_initial'))
        assert_no_cache_header(response)
        assert response.status_code == 200

    @pytest.mark.django_db
    @mock.patch('kuma.payments.views.enabled')
    def test_login_required_recurring_payment_subscription_view_redirect(self, mock_enabled):
        """If enabled, contribution error page is returned."""
        mock_enabled.return_value = True
        response = self.client.get(reverse('recurring_payment_subscription'))
        assert response.status_code == 302

    @pytest.mark.django_db
    @mock.patch('kuma.payments.views.enabled')
    def test_login_required_recurring_payment_subscription_view_ok(self, mock_enabled):
        """If enabled, contribution error page is returned."""
        mock_enabled.return_value = True
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('recurring_payment_subscription'))
        assert_no_cache_header(response)
        assert response.status_code == 200

    @pytest.mark.django_db
    @mock.patch('kuma.payments.views.enabled')
    def test_post_method_redirect_recurring_payment_subscription(self, mock_enabled):
        """If enabled, contribution error page is returned."""
        mock_enabled.return_value = True
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('recurring_payment_subscription'),
            data={
                'name': 'True name',
                'email': 'true.email@mozilla.com',
                'donation_amount': 124,
            }
        )
        assert_no_cache_header(response)
        assert response.status_code == 302
        assert response.url == reverse('payment_error')

    @override_settings(MDN_CONTRIBUTION_CONFIRMATION_EMAIL=False)
    @pytest.mark.django_db
    @mock.patch('kuma.payments.views.enabled')
    @mock.patch('kuma.payments.views.ContributionRecurringPaymentForm.make_recurring_payment_charge', return_value=True)
    def test_post_method_recurring_payment_subscription(self, mock_enabled, form):
        """If enabled, contribution error page is returned."""
        mock_enabled.return_value = True
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('recurring_payment_subscription'),
            data={
                'name': 'True name',
                'email': 'true.email@mozilla.com',
                'donation_amount': 63,
                'stripe_token': 'some-token',
                'stripe_public_key': 'some-public-key',
            }
        )
        assert_no_cache_header(response)
        assert response.status_code == 302
        assert response.url == reverse('payment_succeeded')

    @pytest.mark.django_db
    @mock.patch('kuma.payments.views.enabled')
    def test_template_render_logged_in_recurring_payment_initial_view(self, mock_enabled):
        """If enabled, contribution error page is returned."""
        mock_enabled.return_value = True
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('recurring_payment_initial'))
        assert_no_cache_header(response)
        assert response.status_code == 200
        self.assertContains(response, '<input type="hidden"', 3)
        self.assertContains(response, 'id="id_stripe_token"', 1)
        self.assertContains(response, 'id="stripe_source_setup"', 1)
        self.assertContains(response, 'id="id_stripe_public_key"', 1)
        self.assertContains(response, '<form id="contribute-form"', 1)
        self.assertContains(response, '<input type="email"', 1)
        self.assertContains(response, 'id="id_donation_amount"', 1)
        self.assertContains(response, 'id="id_donation_choices"', 1)

    @pytest.mark.django_db
    @mock.patch('kuma.payments.views.enabled')
    def test_template_render_not_logged_in_recurring_payment_initial_view(self, mock_enabled):
        """If enabled, contribution error page is returned."""
        mock_enabled.return_value = True
        response = self.client.get(reverse('recurring_payment_initial'))
        assert_no_cache_header(response)
        assert response.status_code == 200
        self.assertContains(response, '<input type="hidden"', 1)
        self.assertContains(response, 'id="id_stripe_token"', 0)
        self.assertContains(response, 'id="stripe_source_setup"', 1)
        self.assertContains(response, 'id="id_stripe_public_key"', 0)
        self.assertContains(response, '<form id="contribute-form"', 1)
        self.assertContains(response, '<input type="email"', 1)
        self.assertContains(response, 'id="id_donation_amount"', 1)
        self.assertContains(response, 'id="id_donation_choices"', 1)
