from allauth.account.adapter import DefaultAccountAdapter, get_adapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from waffle import flag_is_active

from kuma.core.urlresolvers import reverse

from .constants import USERNAME_CHARACTERS, USERNAME_REGEX

REMOVE_BUG_URL = "https://bugzilla.mozilla.org/enter_bug.cgi?assigned_to=nobody%40mozilla.org&bug_file_loc=http%3A%2F%2F&bug_ignored=0&bug_severity=normal&bug_status=NEW&cf_fx_iteration=---&cf_fx_points=---&comment=Please%20delete%20my%20MDN%20account.%20My%20username%20is%3A%0D%0A%0D%0A[username]&component=User%20management&contenttypemethod=autodetect&contenttypeselection=text%2Fplain&defined_groups=1&flag_type-4=X&flag_type-607=X&flag_type-791=X&flag_type-800=X&flag_type-803=X&form_name=enter_bug&maketemplate=Remember%20values%20as%20bookmarkable%20template&op_sys=All&priority=--&product=Mozilla%20Developer%20Network&rep_platform=All&short_desc=Account%20deletion%20request%20for%20[username]&status_whiteboard=[account-mod]&target_milestone=---&version=unspecified&format=__standard__"
REMOVE_MESSAGE = _(u"Sorry, you must have at least one connected account so "
                   u"you can sign in. To disconnect this account connect a "
                   u"different one first. To delete your MDN profile please "
                   u'<a href="%(bug_form_url)s" rel="nofollow">file a bug</a>.')
USERNAME_EMAIL = _(u'An email address cannot be used as a username.')


class KumaAccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        """
        We disable the signup with regular accounts as we require GitHub
        (for now)
        """
        return False

    def clean_username(self, username):
        """
        When signing up make sure the username isn't already used by
        a different user, and doesn't contain invalid characters.
        """
        # We have stricter username requirements than django-allauth,
        # because we don't want to allow '@' in usernames. So we check
        # that before calling super() to make sure we catch those
        # problems and show our error messages.
        if '@' in username:
            raise forms.ValidationError(USERNAME_EMAIL)
        if not USERNAME_REGEX.match(username):
            raise forms.ValidationError(USERNAME_CHARACTERS)
        username = super(KumaAccountAdapter, self).clean_username(username)
        if get_user_model().objects.filter(username=username).exists():
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

            # when a next URL is set because of a multi step sign-in
            # (e.g. sign-in with github, verified mail is found in other
            # social accounts, agree to first log in with other to connect
            # instead) and the next URL is not the edit profile page (which
            # would indicate the start of the sign-in process from the edit
            # profile page) we ignore the message "account connected" message
            # as it would be misleading
            # Bug 1229906#c2 - need from "create new account" page
            user_url = reverse('users.user_edit',
                               kwargs={'username': request.user.username},
                               locale=request.LANGUAGE_CODE)
            next_url = request.session.get('sociallogin_next_url', None)
            if next_url != user_url:
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
        allowed = True
        if flag_is_active(request, 'registration_disabled'):
            allowed = False

        # bug 1291892: Don't confuse next login with connecting accounts
        if not allowed:
            for key in ('socialaccount_sociallogin', 'sociallogin_provider'):
                try:
                    del request.session[key]
                except KeyError:  # pragma: no cover
                    pass

        return allowed

    def validate_disconnect(self, account, accounts):
        """
        Validate whether or not the socialaccount account can be
        safely disconnected.
        """
        if len(accounts) == 1:
            raise forms.ValidationError(REMOVE_MESSAGE %
                                        {'bug_form_url': REMOVE_BUG_URL})

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.

        We use it to:
            1. Check if the user is connecting accounts via signup page
            2. store the name of the socialaccount provider in the user's session.
        """
        session_login_data = request.session.get('socialaccount_sociallogin', None)
        request_login = sociallogin

        # Is there already a sociallogin_provider in the session?
        if session_login_data:
            session_login = SocialLogin.deserialize(session_login_data)
            # If the provider in the session is different from the provider in the
            # request, the user is connecting a new provider to an existing account
            if session_login.account.provider != request_login.account.provider:
                # Does the request sociallogin match an existing user?
                if not request_login.is_existing:
                    # go straight back to signup page with an error message
                    # BEFORE allauth over-writes the session sociallogin
                    level = messages.ERROR
                    message = "socialaccount/messages/account_not_found.txt"
                    get_adapter().add_message(request, level, message)
                    raise ImmediateHttpResponse(
                        redirect('socialaccount_signup')
                    )
        # TODO: Can the code that uses this just use request.session['socialaccount_sociallogin'].account.provider instead?
        request.session['sociallogin_provider'] = (sociallogin
                                                   .account.provider)
        request.session.modified = True

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully
        connecting a social account.
        """
        assert request.user.is_authenticated()
        user_url = reverse('users.user_edit',
                           kwargs={'username': request.user.username},
                           locale=request.LANGUAGE_CODE)
        return user_url

    def save_user(self, request, sociallogin, form):
        """
        Update the session after creating a new user account.

        If the socialaccount_sociallogin remains in the session, then the user
        will be unable to connect a second account unless they log out and
        log in again.
        """
        super(KumaSocialAccountAdapter, self).save_user(request, sociallogin,
                                                        form)
        try:
            del request.session['socialaccount_sociallogin']
        except KeyError:  # pragma: no cover
            pass
