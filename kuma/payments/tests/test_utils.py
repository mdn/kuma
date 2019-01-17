import copy

import mock

from kuma.payments.utils import (
    cancel_stripe_customer_subscription,
    get_stripe_customer_data,
    stripe)


class SubscriptionDict(dict):
    """Cheap version of Stripe's Subscription object.

    Allows access like dict (data['id']) or property (data.id)
    """
    @property
    def id(self):
        return self['id']


# Subset of data returned for customer
# https://stripe.com/docs/api/customers/retrieve
simple_customer_data = {
    'sources': {'data': [{'card': {'last4': '0019'}}]},
    'subscriptions': {'data': [SubscriptionDict({
        'id': 'sub_id',
        'plan': {'amount': 6400},
    })]},
}


@mock.patch('stripe.Customer.retrieve', return_value=simple_customer_data)
def test_get_stripe_customer_data(mock_retrieve):
    '''A customer's subscription can be retrieved.'''
    data = get_stripe_customer_data('cust_id', 'beth@example.com', 'beth')
    assert data == {
        'stripe_plan_amount': 64,
        'stripe_card_last4': '0019',
        'active_subscriptions': True
    }


@mock.patch('stripe.Customer.retrieve',
            side_effect=stripe.error.InvalidRequestError('bad stripe ID',
                                                         'id'))
def test_get_stripe_customer_data_invalid_request(mock_retrieve):
    '''Blank info is returned for an invalid request.'''
    data = get_stripe_customer_data('cust_id', 'beth@example.com', 'beth')
    assert data == {
        'stripe_plan_amount': 0,
        'stripe_card_last4': 0,
        'active_subscriptions': False
    }


@mock.patch('stripe.Customer.retrieve')
def test_get_stripe_customer_data_key_error(mock_retrieve):
    '''Exceptions may cause partial data to be returned.'''
    stripe_data = copy.deepcopy(simple_customer_data)
    del stripe_data['sources']  # Will raise KeyError
    mock_retrieve.return_value = stripe_data
    data = get_stripe_customer_data('cust_id', 'beth@example.com', 'beth')
    assert data == {
        'stripe_plan_amount': 64,
        'stripe_card_last4': 0,
        'active_subscriptions': True
    }


@mock.patch('stripe.Customer.retrieve')
def test_get_stripe_customer_data_missing_data(mock_retrieve):
    '''Missing data looks like a missing customer.'''
    stripe_data = {'sources': None, 'subscription': None}
    mock_retrieve.return_value = stripe_data
    data = get_stripe_customer_data('cust_id', 'beth@example.com', 'beth')
    assert data == {
        'stripe_plan_amount': 0,
        'stripe_card_last4': 0,
        'active_subscriptions': False
    }


@mock.patch('stripe.Customer.retrieve', return_value=simple_customer_data)
@mock.patch('stripe.Subscription.retrieve',
            return_value=mock.Mock(spec_set=['delete']))
def test_cancel_stripe_customer_subscription(mock_sub, mock_cust):
    '''A stripe customer's subscriptions can be cancelled.'''
    assert cancel_stripe_customer_subscription('cust_id', 'beth@example.com',
                                               'beth')
    mock_sub.return_value.delete.assert_called_once_with()


@mock.patch('stripe.Customer.retrieve',
            return_value={
                'subscriptions': {'data': [
                    SubscriptionDict({'id': 'sub_id1'}),
                    SubscriptionDict({'id': 'sub_id2'}),
                ]}})
@mock.patch('stripe.Subscription.retrieve',
            side_effect=[mock.Mock(spec_set=['delete']),
                         mock.Mock(spec_set=['delete'])])
def test_cancel_stripe_customer_multiple_subscriptions(mock_sub, mock_cust):
    '''A stripe customer's subscriptions can be cancelled.'''
    assert cancel_stripe_customer_subscription('cust_id', 'beth@example.com',
                                               'beth')
    assert mock_sub.call_count == 2


@mock.patch('stripe.Customer.retrieve',
            return_value={'subscriptions': {'data': []}})
@mock.patch('stripe.Subscription.retrieve', side_effect=Exception('Oops'))
def test_cancel_stripe_customer_no_subscriptions(mock_sub, mock_cust):
    '''A stripe customer with no subscriptions returns True.'''
    assert cancel_stripe_customer_subscription('cust_id', 'beth@example.com',
                                               'beth')
    assert not mock_sub.called


@mock.patch('stripe.Customer.retrieve',
            side_effect=stripe.error.InvalidRequestError('bad stripe ID',
                                                         'id'))
def test_cancel_stripe_customer_invalid_request(mock_cust):
    '''An invalid call to the Stripe API returns False.'''
    assert not cancel_stripe_customer_subscription('cust_id',
                                                   'beth@example.com', 'beth')
    assert mock_cust.called


@mock.patch('stripe.Customer.retrieve', side_effect=ValueError('Oops'))
def test_cancel_stripe_customer_other_exception(mock_cust):
    '''An exception during processing returns False.'''
    assert not cancel_stripe_customer_subscription('cust_id',
                                                   'beth@example.com', 'beth')
    assert mock_cust.called
