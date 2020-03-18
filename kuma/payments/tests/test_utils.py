from unittest import mock

from kuma.payments.utils import (
    cancel_stripe_customer_subscription,
    get_stripe_customer_data,
)


# Subset of data returned for customer
# https://stripe.com/docs/api/customers/retrieve
simple_customer_data = {
    "sources": {"data": [{"card": {"last4": "0019"}, "object": "source"}]},
    "subscriptions": {"data": [{"id": "sub_id", "plan": {"amount": 6400}}]},
}


@mock.patch("stripe.Customer.retrieve", return_value=simple_customer_data)
def test_get_stripe_customer_data(mock_retrieve):
    """A customer's subscription can be retrieved."""
    data = get_stripe_customer_data("cust_id")
    assert data == {
        "stripe_plan_amount": 64,
        "stripe_card_last4": "0019",
        "active_subscriptions": True,
    }


@mock.patch("stripe.Customer.retrieve", return_value=simple_customer_data)
@mock.patch(
    "stripe.Subscription.retrieve", return_value=mock.Mock(spec_set=["delete", "id"])
)
def test_cancel_stripe_customer_subscription(mock_sub, mock_cust):
    """A stripe customer's subscriptions can be cancelled."""
    cancel_stripe_customer_subscription("cust_id")
    mock_sub.return_value.delete.assert_called_once_with()


@mock.patch(
    "stripe.Customer.retrieve",
    return_value={"subscriptions": {"data": [{"id": "sub_id1"}, {"id": "sub_id2"}]}},
)
@mock.patch(
    "stripe.Subscription.retrieve",
    side_effect=[
        mock.Mock(spec_set=["delete", "id"]),
        mock.Mock(spec_set=["delete", "id"]),
    ],
)
def test_cancel_stripe_customer_multiple_subscriptions(mock_sub, mock_cust):
    """A stripe customer's subscriptions can be cancelled."""
    cancel_stripe_customer_subscription("cust_id")
    assert mock_sub.call_count == 2


@mock.patch("stripe.Customer.retrieve", return_value={"subscriptions": {"data": []}})
@mock.patch("stripe.Subscription.retrieve", side_effect=Exception("Oops"))
def test_cancel_stripe_customer_no_subscriptions(mock_sub, mock_cust):
    """A stripe customer with no subscriptions returns True."""
    cancel_stripe_customer_subscription("cust_id")
    assert not mock_sub.called
