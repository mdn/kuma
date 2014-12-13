from django import forms
from django.core import validators

from allauth.socialaccount.forms import SignupForm as BaseSignupForm
from tower import ugettext_lazy as _

USERNAME_REQUIRED = _(u'Username is required.')
USERNAME_SHORT = _(u'Username is too short (%(show_value)s characters). '
                   u'It must be at least %(limit_value)s characters.')
USERNAME_LONG = _(u'Username is too long (%(show_value)s characters). '
                  u'It must be %(limit_value)s characters or less.')

TERMS_REQUIRED = _(u'You must agree to the terms of use.')


class SignupForm(BaseSignupForm):
    """
    The user registration form for allauth.

    This overrides the default error messages for the username form field
    with our own strings.

    It has an additional other_email form field to handle the case of Github
    which may deliver a number of emails for users to choose from upon signup.

    The heavy lifting happens in the view.
    """
    email = forms.CharField(required=False,
                            widget=forms.TextInput(attrs={'type': 'email'}))
    other_email = forms.CharField(required=False,
                                  widget=forms.TextInput(attrs={'type': 'email'}))
    terms = forms.BooleanField(label=_(u'I agree'),
                               required=True,
                               error_messages={'required': TERMS_REQUIRED})
    other_email_value = '_other'
    duplicate_email_error_label = '_duplicate_email'

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.other_email_used = False
        self.fields['username'].error_messages = {
            'required': USERNAME_REQUIRED,
            'min_length': USERNAME_SHORT,
            'max_length': USERNAME_LONG,
        }

    def clean_email(self):
        value = self.cleaned_data['email']
        # if the selected email address is "other" we cut things short
        # and clean the value in the form's clean method instead
        if value == self.other_email_value:
            return value

        # otherwise we emmulate the functionality of the EmailField here
        # stripping whitespaces, validating the content and then
        # run allauth's own email value cleanup
        self.cleaned_data["email"] = value.strip()
        validators.validate_email(value)
        return super(SignupForm, self).clean_email()

    def clean(self):
        """
        Cleans the email field data given the other email address field
        if given.
        """
        cleaned_data = super(SignupForm, self).clean()
        # let's see if the email value was "other"
        if cleaned_data.get('email') == self.other_email_value:
            # and set the cleaned data to the cleaned other_email value
            self.cleaned_data['email'] = self.cleaned_data['other_email']
            # also store the fact of using the other value in an attribute
            # to be used in the view to check for it
            self.other_email_used = True
            # then run the usual email clean method again to apply
            # the regular email validation and put the error into the
            # email field specific value
            try:
                self.clean_email()
            except forms.ValidationError as e:
                self._errors['email'] = self.error_class(e.messages)
        return cleaned_data

    def raise_duplicate_email_error(self):
        raise forms.ValidationError(self.duplicate_email_error_label)
