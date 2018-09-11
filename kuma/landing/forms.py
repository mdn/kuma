import stripe
from django import forms
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _

from kuma.core.form_fields import StrippedCharField

stripe.api_key = settings.STRIPE_SECRET_KEY

CURRENCY = {
    u'USD': u'$'
}

DONATION_CHOICES = [
    (i, u'{}{}'.format(CURRENCY[u'USD'], i)) for i in settings.CONTRIBUTION_FORM_CHOICES
]


class ContributionForm(forms.Form):
    name = StrippedCharField(
        min_length=1,
        max_length=255,
        label=u'',
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Your full name'),
                'data-error-message': _('Required')
            }
        )
    )
    email = forms.EmailField(
        label=u'',
        widget=forms.EmailInput(
            attrs={
                'placeholder': _('you@example.com'),
                'data-error-message': _('Must be a valid email'),
                'title': _('Why do you need my email address? This is so we can send you a receipt of your contribution. This is handy if you would like a refund.')
            }
        )
    )
    donation_choices = forms.TypedChoiceField(
        required=False,
        choices=DONATION_CHOICES,
        widget=forms.RadioSelect(),
        label=u'',
        empty_value=0,
        coerce=int,
        initial=DONATION_CHOICES[1][0]
    )
    donation_amount = forms.DecimalField(
        required=False,
        label=u'$',
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

        if not donation_amount and not donation_choices:
            raise forms.ValidationError(u'Please select donation amount or choose from pre-selected choices')
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
        amount = amount * 100
        token = self.cleaned_data.get('stripe_token', '')
        if False and token and amount:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                source=token,
                description="Contrubute to MDN Web Docs"
            )
        return charge
