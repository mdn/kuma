from unittest import mock

import pytest
from stripe.error import InvalidRequestError

from kuma.users.models import User


@mock.patch("kuma.users.signal_handlers.cancel_stripe_customer_subscriptions")
def test_unsubscribe_payments_on_user_delete(mock_cancel, stripe_user):
    """A stripe subscription is cancelled when the user is deleted."""
    username = stripe_user.username
    stripe_user.delete()
    mock_cancel.assert_called_once_with(stripe_user)
    assert not User.objects.filter(username=username).exists()


@mock.patch(
    "kuma.users.signal_handlers.cancel_stripe_customer_subscriptions",
    side_effect=InvalidRequestError(
        "No such customer: cust_test123",
        param="id",
        code="resourse_missing",
        http_status=404,
    ),
)
def test_unsubscribe_payments_on_user_delete_fails(mock_cancel, stripe_user):
    """If stripe subscription cancellation fails, do not delete User."""
    with pytest.raises(InvalidRequestError):
        stripe_user.delete()
    mock_cancel.assert_called_once_with(stripe_user)
