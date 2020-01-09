from datetime import datetime
from unittest import mock

import pytest
from stripe.error import InvalidRequestError

from kuma.users.models import User


@pytest.fixture
def payments_user(db, django_user_model):
    return User.objects.create(
        username='payments_user',
        email='payer@example.com',
        date_joined=datetime(2019, 1, 17, 15, 42),
        stripe_customer_id='cust_test123')


@mock.patch('kuma.users.signal_handlers.cancel_stripe_customer_subscription')
def test_unsubscribe_payments_on_user_delete(mock_cancel, payments_user):
    """A stripe subscription is cancelled when the user is deleted."""
    payments_user.delete()
    mock_cancel.assert_called_once_with('cust_test123')
    assert not User.objects.filter(username='payments_user').exists()


@mock.patch('kuma.users.signal_handlers.cancel_stripe_customer_subscription',
            side_effect=InvalidRequestError(
                'No such customer: cust_test123',
                param='id',
                code='resourse_missing',
                http_status=404))
def test_unsubscribe_payments_on_user_delete_fails(mock_cancel, payments_user):
    """If stripe subscription cancellation fails, do not delete User."""
    with pytest.raises(InvalidRequestError):
        payments_user.delete()
    mock_cancel.assert_called_once_with('cust_test123')
