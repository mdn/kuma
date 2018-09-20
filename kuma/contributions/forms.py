from __future__ import unicode_literals

from decimal import Decimal

import stripe
from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _

from kuma.core.form_fields import StrippedCharField

stripe.api_key = settings.STRIPE_SECRET_KEY

CURRENCY = {
    'USD': '$'
}

DONATION_CHOICES = [
    (i, '{}{}'.format(CURRENCY['USD'], i)) for i in settings.CONTRIBUTION_FORM_CHOICES
]


class ContributionForm(forms.Form):
    name = StrippedCharField(
        min_length=1,
        max_length=255,
        label=_('Your full name'),
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Your full name'),
                'data-error-message': _('Required')
            }
        )
    )
    email = forms.EmailField(
        label=_('Your email'),
        widget=forms.EmailInput(
            attrs={
                'placeholder': _('you@example.com'),
                'data-error-message': _('Must be a valid email'),
                'title': _('Why do you need my email address? This is so we'
                           ' can send you a receipt of your contribution. This'
                           ' is handy if you would like a refund.')
            }
        )
    )
    donation_choices = forms.TypedChoiceField(
        required=False,
        choices=DONATION_CHOICES,
        widget=forms.RadioSelect(),
        label=_('Contribution choices'),
        empty_value=0,
        coerce=int,
        initial=DONATION_CHOICES[1][0]
    )
    donation_amount = forms.DecimalField(
        required=False,
        label='$',
        max_digits=10,
        decimal_places=2,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Other amount'),
                'data-error-message': _('Must be more than $1')
            }
        ),
        validators=[MinValueValidator(1)]
    )
    stripe_token = forms.CharField(
        label=u'',
        required=False,
        widget=forms.HiddenInput(),
        max_length=255
    )
    stripe_public_key = forms.CharField(
        label=u'',
        required=False,
        widget=forms.HiddenInput(),
        max_length=255
    )

    def clean(self):
        d = self.cleaned_data
        donation_choices = d.get('donation_choices', False)
        donation_amount = d.get('donation_amount', False)

        if not donation_amount and not donation_choices or donation_amount and donation_choices:
            raise forms.ValidationError('Please select donation amount or'
                                        ' choose from pre-selected choices')
        return d

    def __init__(self, *args, **kwargs):
        super(ContributionForm, self).__init__(*args, **kwargs)
        self.fields['stripe_public_key'].initial = settings.STRIPE_PUBLIC_KEY

    def make_charge(self):
        charge = {
            'id': '',
            'status': ''
        }
        amount = self.cleaned_data['donation_amount'] or self.cleaned_data['donation_choices']
        if isinstance(amount, Decimal):
            amount = amount * Decimal('100')
            amount = amount.quantize(Decimal('0'))
        else:
            amount = amount * 100
        token = self.cleaned_data.get('stripe_token', '')
        if token and amount:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                source=token,
                description="Contribute to MDN Web Docs"
            )
        return charge
