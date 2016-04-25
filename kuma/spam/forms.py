from django import forms
from django.utils.translation import ugettext_lazy as _
from waffle import flag_is_active

from . import akismet, constants


class AkismetFormMixin(object):
    akismet_error_message = _('The submitted data contains invalid content.')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self._client = akismet.Akismet()
        super(AkismetFormMixin, self).__init__(*args, **kwargs)

    @property
    def akismet_client(self):
        return self._client

    @akismet_client.setter
    def akismet_client(self, value):
        self._client = value

    def akismet_enabled(self):
        """
        Decides whether to even check for spam during the form validation.

        Checks the API client if it's ready by default.
        """
        return self.akismet_client.ready

    def akismet_error(self, parameters, exception=None):
        """
        Upon receiving an error from the API client raises an "invalid"
        form validation error with a predefined error message.
        """
        raise forms.ValidationError(self.akismet_error_message, code='invalid')

    def akismet_call(self):
        """
        The method to be called as part of the form field validation.
        It needs to be implemented in subclasses of this class.
        """
        raise NotImplementedError

    def akismet_parameters(self):
        """
        When calling the akismet client as part of the form field validation
        this method shall return the parameters to be passed during the
        Akismet client call.
        """
        raise NotImplementedError

    def akismet_parameter_overrides(self):
        """
        Get parameter overrides based on user's waffle flags.
        """
        parameters = {}
        if flag_is_active(self.request, constants.SPAM_ADMIN_FLAG):
            parameters['user_role'] = 'administrator'
        if flag_is_active(self.request, constants.SPAM_SPAMMER_FLAG):
            parameters['comment_author'] = 'viagra-test-123'
        if flag_is_active(self.request, constants.SPAM_TESTING_FLAG):
            parameters['is_test'] = True
        return parameters

    def clean(self):
        cleaned_data = super(AkismetFormMixin, self).clean()
        if self.akismet_enabled():
            self.akismet_call(self.akismet_parameters())
        return cleaned_data


class AkismetCheckFormMixin(AkismetFormMixin):
    """
    The main form mixin for Akismet checks.

    Form classes using this can reimplement the methods starting with
    "akismet_" below to extend its functionality.
    """

    def akismet_enabled(self):
        """
        Decides whether to even check for spam during the form validation.

        Checks the waffle flag additionally to the default behavior.
        """
        spam_checks = flag_is_active(self.request, constants.SPAM_CHECKS_FLAG)
        return (spam_checks and
                super(AkismetCheckFormMixin, self).akismet_enabled())

    def akismet_call(self, parameters):
        try:
            is_spam = self.akismet_client.check_comment(**parameters)
        except akismet.AkismetError as exception:
            self.akismet_error(parameters, exception)
        else:
            if is_spam:
                self.akismet_error(parameters)


class AkismetSubmissionFormMixin(AkismetFormMixin):
    akismet_error_message = _('The submitted data contains invalid content. '
                              'Please try again.')

    def akismet_enabled(self):
        """
        Decides whether to even check for spam during the form validation.

        Checks the API client if it's ready by default.
        """
        spam_submission = flag_is_active(
            self.request,
            constants.SPAM_SUBMISSIONS_FLAG
        )
        return (
            spam_submission and
            super(AkismetSubmissionFormMixin, self).akismet_enabled()
        )

    def akismet_submission_type(self):
        """
        Used in the ``akismet_call`` method to decide which submission
        function to use in the Akismet client.
        """
        raise NotImplementedError

    def akismet_call(self, parameters):
        """"
        Get the submission function and call it with the parameters.
        """
        submission_function = 'submit_%s' % self.akismet_submission_type()
        try:
            getattr(self.akismet_client, submission_function)(**parameters)
        except akismet.AkismetError as exception:
            self.akismet_error(parameters, exception)
