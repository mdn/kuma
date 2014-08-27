from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from tower import ugettext_lazy as _

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


REMOVE_BUG_URL = "https://bugzilla.mozilla.org/enter_bug.cgi?assigned_to=nobody%40mozilla.org&bug_file_loc=http%3A%2F%2F&bug_ignored=0&bug_severity=normal&bug_status=NEW&cf_fx_iteration=---&cf_fx_points=---&comment=Please%20delete%20my%20MDN%20account.%20My%20username%20is%3A%0D%0A%0D%0A[username]&component=User%20management&contenttypemethod=autodetect&contenttypeselection=text%2Fplain&defined_groups=1&flag_type-4=X&flag_type-607=X&flag_type-791=X&flag_type-800=X&flag_type-803=X&form_name=enter_bug&maketemplate=Remember%20values%20as%20bookmarkable%20template&op_sys=All&priority=--&product=Mozilla%20Developer%20Network&rep_platform=All&short_desc=Account%20deletion%20request%20for%20[username]&status_whiteboard=[account-mod]&target_milestone=---&version=unspecified&format=__standard__"
REMOVE_MESSAGE = _(u"Sorry, you must have at least one connected account so "
                   u"you can log in. To remove this account connect a "
                   u"different one first. To delete your MDN account please "
                   u'<a href="%(bug_form_url)s" rel="nofollow">file a bug</a>.')


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

    def message_templates(self, *names):
        return tuple('messages/%s.txt' % name for name in names)

    def add_message(self, request, level, message_template,
                    message_context={}, extra_tags='', *args, **kwargs):
        """
        Adds an extra "account" tag to the success and error messages.
        """
        # let's ignore some messages
        if message_template.endswith(self.message_templates('logged_in',
                                                            'logged_out')):
            return

        # promote the "account_connected" message to success
        if message_template.endswith(self.message_templates('account_connected')):
            level = messages.SUCCESS

            # when a next url is set because of a multi step sign-in
            # (e.g. sign-in with github, verified mail is found in Persona
            # social accounts, agree to first log in with Persona to connect
            # instead) we ignore the message "account connected" message as
            # it would be misleading
            if 'sociallogin_next_url' in request.session:
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
            raise forms.ValidationError(REMOVE_MESSAGE %
                                        {'bug_form_url': REMOVE_BUG_URL})
