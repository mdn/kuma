from django import forms
from django.contrib.auth.models import User

from tower import ugettext_lazy as _

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class KumaAccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        """
        We disable the signup with regular accounts as we require Persona
        (for now)
        """
        return False

    def clean_username(self, username):
        """
        When signing up make sure the username isn't already used by
        a different user.
        """
        username = super(KumaAccountAdapter, self).clean_username(username)
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_(u'The username you entered '
                                          u'already exists.'))
        return username

    def add_message(self, request, level, message_template,
                    message_context={}, extra_tags='', *args, **kwargs):
        """
        Adds an extra "account" tag to the success and error messages.
        """
        # let's ignore some messages
        unwanted = ('logged_in', 'logged_out')
        if message_template.endswith(tuple(['messages/%s.txt' % name
                                            for name in unwanted])):
            return
        # and add an extra tag to the account messages
        extra_tag = 'account'
        if extra_tags:
            extra_tags += ' '
        extra_tags += extra_tag
        super(KumaAccountAdapter, self).add_message(request, level,
                                                    message_template,
                                                    message_context,
                                                    extra_tags,
                                                    *args, **kwargs)


class KumaSocialAccountAdapter(DefaultSocialAccountAdapter):

    def is_open_for_signup(self, request, sociallogin):
        """
        We specifically enable social accounts as a way to signup
        because the default adapter uses the account adpater above
        as the default.
        """
        return True

    def validate_disconnect(self, account, accounts):
        """
        Validate whether or not the socialaccount account can be
        safely disconnected.
        """
        if len(accounts) == 1:
            raise forms.ValidationError(_(u"You cannot remove your only account."))
