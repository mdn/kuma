from django import forms

from tower import ugettext as _, ugettext_lazy as _lazy

EMAIL_REQUIRED = _lazy(u'Email address is required.')
EMAIL_SHORT = _lazy(u'Email address is too short (%(show_value)s characters). '
                    'It must be at least %(limit_value)s characters.')
EMAIL_LONG = _lazy(u'Email address is too long (%(show_value)s characters). '
                   'It must be %(limit_value)s characters or less.')
PRIVACY_REQUIRED = _lazy(u'You must agree to the privacy policy.')

class SubscriptionForm(forms.Form):
    """
    Form to capture and validate email subscriptions
    """
    email = forms.EmailField(label=_lazy(u'Your e-mail address'),
                             error_messages={'required': EMAIL_REQUIRED,
                                             'min_length': EMAIL_SHORT,
                                             'max_length': EMAIL_LONG})
    format = forms.ChoiceField(
        label=_lazy(u'Your preferred format'),
        choices=[('html', 'HTML'), ('text', 'Plain text')],
        widget=forms.RadioSelect()
    )
    agree = forms.BooleanField(
        label=_lazy(u'I agree'),
        error_messages={'required': PRIVACY_REQUIRED}
    )
