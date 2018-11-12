from __future__ import unicode_literals

import logging
from decimal import Decimal

import stripe
from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _

from kuma.core.form_fields import StrippedCharField

log = logging.getLogger('kuma.payments.forms')


stripe.api_key = settings.STRIPE_SECRET_KEY

CURRENCY = {
    'USD': '$'
}

DONATION_CHOICES = [
    (i, '{}{}'.format(CURRENCY['USD'], i)) for i in settings.CONTRIBUTION_FORM_CHOICES
]

RECURRING_PAYMENT__CHOICES = [
    (i, '{}{}/mo'.format(CURRENCY['USD'], i)) for i in settings.RECURRING_PAYMENT_FORM_CHOICES
]

STRIPE_MONTHLY_PLAN_ID_TEMPLATE = 'plan_monthly_{amount}_usd'


class ContributionForm(forms.Form):
    name = StrippedCharField(
        min_length=1,
        max_length=255,
        label=_('Your full name'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-input form-input-email',
                'placeholder': _('Your full name'),
                'data-error-message': _('Required')
            }
        )
    )
    email = forms.EmailField(
        label=_('Your email'),
        widget=forms.EmailInput(
            attrs={
                'class': 'form-input form-input-email',
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
        label=_('Contribution choices'),
        empty_value=0,
        coerce=int,
        initial=DONATION_CHOICES[1][0],
        widget=forms.RadioSelect(
            attrs={
                'class': 'form-radios form-radios-donation-choices'
                'data-dynamic-choice-selector'
            }
        )
    )
    donation_amount = forms.DecimalField(
        required=False,
        label='$',
        max_digits=10,
        decimal_places=2,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input form-input-amount',
                'placeholder': _('Other'),
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

    accept_checkbox = forms.BooleanField(
        label=u'',
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'required checkbox form-control',
                'data-error-message': _('You must agree to the terms to continue')
            },
        ),
    )

    def clean(self):
        """Validate that either an amount or set choice was made."""
        d = self.cleaned_data
        donation_choice = d.get('donation_choices', False)
        donation_amount = d.get('donation_amount', False)

        no_selection = not (donation_amount or donation_choice)
        both_selections = donation_amount and donation_choice
        if no_selection or both_selections:
            raise forms.ValidationError(_('Please select donation amount or'
                                          ' choose from pre-selected choices'))
        return d

    def __init__(self, *args, **kwargs):
        super(ContributionForm, self).__init__(*args, **kwargs)
        self.fields['stripe_public_key'].initial = settings.STRIPE_PUBLIC_KEY

    def get_amount(self):
        amount = self.cleaned_data['donation_amount'] or self.cleaned_data['donation_choices']
        if isinstance(amount, Decimal):
            amount = amount * Decimal('100')
            amount = amount.quantize(Decimal('0'))
        else:
            amount = amount * 100
        return amount

    def get_token(self):
        token = self.cleaned_data.get('stripe_token', '')
        if not token:
            log.error(
                'Stripe error!, something went wrong, cant find STRIPE_TOKEN for {} [{}]'.format(
                    self.cleaned_data['name'],
                    self.cleaned_data['email']
                )
            )
        return token

    def make_charge(self):
        """Make a charge using the Stripe API and validated form."""
        amount = self.get_amount()
        token = self.get_token()
        if token and amount:
            try:
                stripe.Charge.create(
                    amount=amount,
                    currency='usd',
                    source=token,
                    description='Support MDN Web Docs',
                    receipt_email=self.cleaned_data['email'],
                    metadata={'name': self.cleaned_data['name']}
                )
                return True
            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                log.error("""
Status is: {http_status}
Type is: {type}
Code is: {code}
Param is: {param}
Message is: {message}
User name: {name}
User email: {email}""".format(**{
                    'http_status': e.http_status,
                    'type': err.get('type'),
                    'code': err.get('code'),
                    'param': err.get('param'),
                    'message': err.get('message'),
                    'name': self.cleaned_data['name'],
                    'email': self.cleaned_data['email']
                }))
            except stripe.error.RateLimitError as e:
                log.error(
                    'Stripe: Too many requests made to the API too quickly: {} [{}] {}'.format(
                        self.cleaned_data['name'],
                        self.cleaned_data['email'],
                        e
                    )
                )
            except stripe.error.InvalidRequestError as e:
                log.error(
                    'Stripe: Invalid parameters were supplied to Stripe API: {} [{}] {}'.format(
                        self.cleaned_data['name'],
                        self.cleaned_data['email'],
                        e
                    )
                )
            except stripe.error.AuthenticationError as e:
                log.error(
                    'Stripe: Authentication with Stripe API failed (maybe you changed API keys recently)): ' +
                    '{} [{}] {}'.format(
                        self.cleaned_data['name'],
                        self.cleaned_data['email'],
                        e
                    )
                )
            except stripe.error.APIConnectionError as e:
                log.error(
                    'Stripe: Network communication with Stripe failed: {} [{}] {}'.format(
                        self.cleaned_data['name'],
                        self.cleaned_data['email'],
                        e
                    )
                )
            except Exception as e:
                log.error(
                    'Stripe charge, something went wrong: {} [{}] {}'.format(
                        self.cleaned_data['name'],
                        self.cleaned_data['email'],
                        e
                    )
                )
        return False


class RecurringPaymentForm(ContributionForm):

    def __init__(self, *args, **kwargs):
        super(RecurringPaymentForm, self).__init__(*args, **kwargs)
        self.fields['donation_choices'].choices = RECURRING_PAYMENT__CHOICES
        self.fields['accept_checkbox'].required = True

    @staticmethod
    def create_customer(email, token, user, name):
        customer = stripe.Customer.create(
            description=name,
            email=email,
            source=token,
            metadata={'name': name}
        )
        user.stripe_customer_id = customer.id
        user.save()
        return customer.id

    @staticmethod
    def update_source_name(source_id, name):
        """Updates the source name with the users defined name"""
        source = stripe.Source.retrieve(source_id)
        source.owner["name"] = name
        source.save()

    def make_recurring_payment_charge(self, user, update_source_name=False):
        amount = self.get_amount()
        token = self.get_token()
        try:
            if token and amount:
                if user.stripe_customer_id:
                    # ensure that customer is active
                    customer = stripe.Customer.retrieve(user.stripe_customer_id)
                    # if deleted make a new customer
                    if 'deleted' in customer:
                        customer_id = self.create_customer(
                            self.cleaned_data['email'],
                            token,
                            user,
                            self.cleaned_data['name']
                        )
                    else:
                        customer_id = user.stripe_customer_id
                else:
                    customer_id = self.create_customer(
                        self.cleaned_data['email'],
                        token,
                        user,
                        self.cleaned_data['name']
                    )

                if update_source_name:
                    self.update_source_name(
                        token,
                        self.cleaned_data['name']
                    )
                plan_id = STRIPE_MONTHLY_PLAN_ID_TEMPLATE.format(**{'amount': amount})
                try:
                    plan = stripe.Plan.retrieve(plan_id)
                except stripe.error.InvalidRequestError:
                    plan = stripe.Plan.create(
                        id=plan_id,
                        amount=amount,
                        interval="month",
                        product=settings.STRIPE_PRODUCT_ID,
                        currency="usd",
                    )
                stripe.Subscription.create(
                    customer=customer_id,
                    billing='charge_automatically',
                    items=[
                        {
                            "plan": plan.id,
                        },
                    ]
                )
                return True
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            log.error("""
Status is: {http_status}
Type is: {type}
Code is: {code}
Param is: {param}
Message is: {message}
User name: {name}
User email: {email}""".format(**{
                'http_status': e.http_status,
                'type': err.get('type'),
                'code': err.get('code'),
                'param': err.get('param'),
                'message': err.get('message'),
                'name': self.cleaned_data['name'],
                'email': self.cleaned_data['email']
            }))
        except stripe.error.RateLimitError as e:
            log.error(
                'Stripe: Too many requests made to the API too quickly: {} [{}] {}'.format(
                    self.cleaned_data['name'],
                    self.cleaned_data['email'],
                    e
                )
            )
        except stripe.error.InvalidRequestError as e:
            log.error(
                'Stripe: Invalid parameters were supplied to Stripe API: {} [{}] {}'.format(
                    self.cleaned_data['name'],
                    self.cleaned_data['email'],
                    e
                )
            )
        except stripe.error.AuthenticationError as e:
            log.error(
                'Stripe: Authentication with Stripe API failed (maybe you changed API keys recently)): ' +
                '{} [{}] {}'.format(
                    self.cleaned_data['name'],
                    self.cleaned_data['email'],
                    e
                )
            )
        except stripe.error.APIConnectionError as e:
            log.error(
                'Stripe: Network communication with Stripe failed: {} [{}] {}'.format(
                    self.cleaned_data['name'],
                    self.cleaned_data['email'],
                    e
                )
            )
        except Exception as e:
            log.error(
                'Stripe charge, something went wrong: {} [{}] {}'.format(
                    self.cleaned_data['name'],
                    self.cleaned_data['email'],
                    e
                )
            )
        return False
