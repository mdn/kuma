import waffle
from django import forms
from django.utils.translation import ugettext_lazy as _

from . import akismet, constants


class AkismetFormMixin(object):
    """
    The main form mixin for Akismet checks.

    Form classes using this can reimplement the methods starting with
    "akismet_" below to extend its functionality.
    """
    akismet_client = akismet.Akismet()
    akismet_error_message = _('The submitted data contains invalid content.')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(AkismetFormMixin, self).__init__(*args, **kwargs)

    def akismet_parameters(self):
        """
        When using this mixin make sure you implement this method,
        get the parent class' value and return a dictionary of
        parameters matching the ones of the Akismet.check_comment method.

        Use the self.instance or self.request variables to build it.
        """
        if not hasattr(self, 'cleaned_data'):
            raise forms.ValidationError(
                _('The form data has not yet been validated. '
                  'Please try again.')
            )
        return {
            'user_ip': self.request.META.get('REMOTE_ADDR', ''),
            'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
            'referrer': self.request.META.get('HTTP_REFERER', ''),
        }

    def akismet_enabled(self):
        """
        Decides whether to even check for spam during the form validation.

        Checks the API client if it's ready by default.
        """
        spam_checks_enabled = waffle.flag_is_active(self.request,
                                                    constants.SPAM_CHECKS_FLAG)
        return (spam_checks_enabled and self.akismet_client.ready)

    def akismet_error(self):
        """
        Upon receiving an error from the API client raises an "invalid"
        form validation error with a predefined error message.
        """
        raise forms.ValidationError(self.akismet_error_message, code='invalid')

    def clean(self):
        cleaned_data = super(AkismetFormMixin, self).clean()
        if self.akismet_enabled():
            akismet_parameters = self.akismet_parameters()
            try:
                self.akismet_client.check_comment(**akismet_parameters)
            except akismet.AkismetError:
                self.akismet_error()
        return cleaned_data
