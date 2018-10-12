from decimal import Decimal

import mock
import pytest

from django.forms.forms import NON_FIELD_ERRORS

from kuma.payments.forms import ContributionForm, DONATION_CHOICES


CONTRIBUTION_FORM_SUCCESS = {
    'custom_amount': (
        {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'donation_amount': 10,
        }, Decimal(1000)),
    'selected_amount': (
        {
            'name': 'John Doe',
            'email': 'john@example.com',
            'donation_choices': DONATION_CHOICES[0][0]
        }, DONATION_CHOICES[0][0] * 100),
}


@pytest.mark.parametrize('data, amount',
                         list(CONTRIBUTION_FORM_SUCCESS.values()),
                         ids=list(CONTRIBUTION_FORM_SUCCESS.keys()))
def test_valid_data(data, amount):
    """Valid data can be charged."""
    form_data = data.copy()
    form_data['stripe_token'] = 'pk_test_token'
    form = ContributionForm(data=form_data)
    assert form.is_valid()

    fake_return = True
    with mock.patch('kuma.payments.forms'
                    '.stripe.Charge.create') as mock_create:
        mock_create.return_value = fake_return
        charge = form.make_charge()
    assert charge == fake_return
    mock_create.assert_called_once_with(
        amount=amount,
        currency='usd',
        description='Support MDN Web Docs',
        metadata={'name': form_data['name']},
        receipt_email=form_data['email'],
        source=form_data['stripe_token'])


def test_no_charge_without_token():
    """Without a token, a charge is not made."""
    data = CONTRIBUTION_FORM_SUCCESS['custom_amount'][0]
    form = ContributionForm(data=data)
    assert form.is_valid()

    with mock.patch('kuma.payments.forms'
                    '.stripe.Charge.create') as mock_create:
        mock_create.side_effect = Exception('Not Called')
        charge = form.make_charge()
    assert charge is False


CONTRIBUTION_FORM_INVALID = {
    'no_amount': (
        {
            'name': 'Fredrick Nihil',
            'email': 'fnihil@example.com',
        }, [NON_FIELD_ERRORS]),
    'both_amounts': (
        {
            'name': 'Whynot All',
            'email': 'whynot@example.com',
            'donation_amount': 10,
            'donation_choices': DONATION_CHOICES[1][0]
        }, [NON_FIELD_ERRORS]),
    'bad_email': (
        {
            'name': 'No Email Please',
            'email': 'no_email@none',
            'donation_amount': 100
        }, ['email']),
    'string_donation': (
        {
            'name': 'Dr. Evil',
            'email': 'drevil@example.com',
            'donation_amount': 'ONE MILLION DOLLARS'
        }, ['donation_amount', NON_FIELD_ERRORS])
}


@pytest.mark.parametrize('data, errored_fields',
                         list(CONTRIBUTION_FORM_INVALID.values()),
                         ids=list(CONTRIBUTION_FORM_INVALID.keys()))
def test_invalid_data(data, errored_fields):
    """ContributionForm.is_valid() is False for bad data."""
    form = ContributionForm(data=data)
    assert not form.is_valid()
    errors = form.errors.as_data()
    assert set(errors.keys()) == set(errored_fields)
