from django import forms
from tower import ugettext_lazy as _
from product_details import product_details


EMAIL_REQUIRED = _(u'Email address is required.')
EMAIL_SHORT = _(u'Email address is too short (%(show_value)s characters). '
                    'It must be at least %(limit_value)s characters.')
EMAIL_LONG = _(u'Email address is too long (%(show_value)s characters). '
                   'It must be %(limit_value)s characters or less.')
PRIVACY_REQUIRED = _(u'You must agree to the privacy policy.')


class SubscriptionForm(forms.Form):
    """
    Form to capture and validate email subscriptions
    """
    email = forms.EmailField(label=_(u'E-mail address'),
                             error_messages={'required': EMAIL_REQUIRED,
                                             'min_length': EMAIL_SHORT,
                                             'max_length': EMAIL_LONG})

    formatChoices = [('html', 'HTML'), ('text', 'Plain text')]
    format = forms.ChoiceField(
        label=_(u'Preferred format'),
        choices=formatChoices,
        initial=formatChoices[0],
        widget=forms.RadioSelect()
    )
    agree = forms.BooleanField(
        label=_(u'I agree'),
        error_messages={'required': PRIVACY_REQUIRED}
    )

    def __init__(self, locale, *args, **kwargs):
        regions = product_details.get_regions(locale)
        regions = sorted(regions.iteritems(), key=lambda x: x[1])

        lang = country = locale.lower()
        if '-' in lang:
            lang, country = lang.split('-', 1)

        super(SubscriptionForm, self).__init__(*args, **kwargs)

        self.fields['country'] = forms.ChoiceField(
            label=_(u'Your country'),
            choices=regions,
            initial=country,
            required=False
        )
