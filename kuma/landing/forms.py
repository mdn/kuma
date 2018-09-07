import stripe
from django import forms
from django.conf import settings
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
        min_length=1, max_length=255,
        label=_(u'Name:')
    )
    email = forms.EmailField(
        label=_(u'Email:')
    )
    donation_choices = forms.TypedChoiceField(
        required=False,
        choices=DONATION_CHOICES,
        widget=forms.RadioSelect(),
        label=u'',
        empty_value=0,
        coerce=int
    )
    donation_amount = forms.DecimalField(
        required=False,
        label=u''
    )
    stripe_token = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        max_length=255
    )
    stripe_public_key = forms.CharField(
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
        if token and amount:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                source=token,
                description="Contrubute to MDN Web Docs"
            )
        return charge
