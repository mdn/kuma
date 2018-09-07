from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from kuma.core.form_fields import StrippedCharField

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
    donation_choices = forms.ChoiceField(
        required=False,
        choices=DONATION_CHOICES,
        widget=forms.RadioSelect(),
        label=u''
    )
    donation_amount = forms.DecimalField(
        required=False,
        label=u''
    )
    stripe_public_key = forms.CharField(required=False, widget=forms.HiddenInput(), max_length=255)
    

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
