from allauth.socialaccount.forms import SignupForm as BaseSignupForm
from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _


USERNAME_REQUIRED = _("Username is required.")
USERNAME_SHORT = _(
    "Username is too short (%(show_value)s characters). "
    "It must be at least %(limit_value)s characters."
)
USERNAME_LONG = _(
    "Username is too long (%(show_value)s characters). "
    "It must be %(limit_value)s characters or less."
)

TERMS_REQUIRED = _("You must agree to the terms of use.")


class SignupForm(BaseSignupForm):
    """
    The user registration form for allauth.

    This overrides the default error messages for the username form field
    with our own strings.

    The heavy lifting happens in the view.
    """

    terms = forms.BooleanField(
        label=_("I agree"), required=True, error_messages={"required": TERMS_REQUIRED}
    )
    is_github_url_public = forms.BooleanField(
        label=_("I would like to make my GitHub profile URL public"), required=False
    )
    is_newsletter_subscribed = forms.BooleanField(required=False)
    duplicate_email_error_label = "_duplicate_email"

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields["username"].error_messages = {
            "required": USERNAME_REQUIRED,
            "min_length": USERNAME_SHORT,
            "max_length": USERNAME_LONG,
        }

    def clean_email(self):
        value = self.cleaned_data["email"]
        validators.validate_email(value)
        return super(SignupForm, self).clean_email()

    def raise_duplicate_email_error(self):
        raise forms.ValidationError(self.duplicate_email_error_label)
