from smtplib import SMTPConnectError, SMTPServerDisconnected

from allauth.account.adapter import DefaultAccountAdapter, get_adapter
from allauth.account.models import EmailAddress
from allauth.account.utils import cleanup_email_addresses
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.cache import add_never_cache_headers
from django.utils.http import is_safe_url
from django.utils.translation import gettext_lazy as _
from redo import retrying

from kuma.core.ga_tracking import (
    ACTION_SOCIAL_AUTH_ADD,
    CATEGORY_SIGNUP_FLOW,
    track_event,
)

from .constants import USERNAME_CHARACTERS, USERNAME_REGEX
from .models import UserBan

REMOVE_BUG_URL = (
    "https://bugzilla.mozilla.org/enter_bug.cgi?"
    "&product=developer.mozilla.org"
    "&component=User%20management"
    "&short_desc=Account%20deletion%20request%20for%20[username]"
    "&comment=Please%20delete%20my%20MDN%20account.%20My%20username%20is%3A"
    "%0D%0A%0D%0A[username]"
    "&status_whiteboard=[account-mod]"
    "&defined_groups=1"
    "&groups=mozilla-employee-confidential"
)
REMOVE_MESSAGE = _(
    "Sorry, you must have at least one connected account so "
    "you can sign in. To disconnect this account connect a "
    "different one first. To delete your MDN profile please "
    '<a href="%(bug_form_url)s" rel="nofollow">file a bug</a>.'
)
USERNAME_EMAIL = _("An email address cannot be used as a username.")


class KumaAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        We disable the signup with regular accounts as we require GitHub
        (for now)
        """
        return False

    def is_safe_url(self, url):
        """This method override exists for 1 single purpose; to make an exception
        for the Yari development server."""
        # The only difference between our override and the one in allauth is that
        # we inject the extra `allowed_hosts=` which, in allauth, is hardcoded to
        # be `allowed_hosts=None`.
        allowed_hosts = None
        if settings.DEBUG:
            allowed_hosts = settings.ADDITIONAL_NEXT_URL_ALLOWED_HOSTS
        return is_safe_url(url, allowed_hosts=allowed_hosts)

    def clean_username(self, username):
        """
        When signing up make sure the username isn't already used by
        a different user, and doesn't contain invalid characters.
        """
        # We have stricter username requirements than django-allauth,
        # because we don't want to allow '@' in usernames. So we check
        # that before calling super() to make sure we catch those
        # problems and show our error messages.
        if "@" in username:
            raise forms.ValidationError(USERNAME_EMAIL)
        if not USERNAME_REGEX.match(username):
            raise forms.ValidationError(USERNAME_CHARACTERS)
        username = super(KumaAccountAdapter, self).clean_username(username)
        if get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError(
                _("The username you entered " "already exists.")
            )
        return username

    def message_templates(self, *names):
        return tuple("messages/%s.txt" % name for name in names)

    def add_message(
        self,
        request,
        level,
        message_template,
        message_context={},
        extra_tags="",
        *args,
        **kwargs,
    ):
        """
        Adds an extra "account" tag to the success and error messages.
        """
        # let's ignore some messages
        if message_template.endswith(
            self.message_templates("logged_in", "logged_out", "account_connected")
        ):
            return

        # and add an extra tag to the account messages
        extra_tag = "account"
        if extra_tags:
            extra_tags += " "
        extra_tags += extra_tag

        super(KumaAccountAdapter, self).add_message(
            request,
            level,
            message_template,
            message_context,
            extra_tags,
            *args,
            **kwargs,
        )

    def save_user(self, request, user, form, commit=True):
        super(KumaAccountAdapter, self).save_user(request, user, form, commit=False)
        is_github_url_public = form.cleaned_data.get("is_github_url_public")
        user.is_github_url_public = is_github_url_public
        user.is_newsletter_subscribed = form.cleaned_data.get(
            "is_newsletter_subscribed", False
        )

        if commit:  # pragma: no cover
            # commit will be True, unless extended by a derived class
            user.save()
        return user

    def send_mail(self, *args, **kwargs):
        retry_options = {
            "retry_exceptions": (SMTPConnectError, SMTPServerDisconnected),
            # The default in redo is 60 seconds. Let's tone that down.
            "sleeptime": 3,
            "attempts": 10,
        }
        parent_method = super(KumaAccountAdapter, self).send_mail
        with retrying(parent_method, **retry_options) as method:
            return method(*args, **kwargs)


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
            raise forms.ValidationError(
                REMOVE_MESSAGE % {"bug_form_url": REMOVE_BUG_URL}
            )

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.

        We use it to:
            1. Check if the user is connecting accounts via signup page
            2. store the name of the socialaccount provider in the user's session.

        TODO: When legacy Persona sessions are cleared (Nov 1 2016), this
        function can be simplified.
        """
        session_login_data = request.session.get("socialaccount_sociallogin", None)
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
                    raise ImmediateHttpResponse(redirect("socialaccount_signup"))

        # Is the user banned?
        if sociallogin.is_existing:
            bans = UserBan.objects.filter(user=sociallogin.user, is_active=True)
            if bans.exists():
                banned_response = render(
                    request,
                    "users/user_banned.html",
                    {"bans": bans, "path": request.path},
                )
                add_never_cache_headers(banned_response)
                raise ImmediateHttpResponse(banned_response)

        # sociallogin_provider is used in the UI to indicate what method was
        # used to login to the website. The session variable
        # 'socialaccount_sociallogin' has the same data, but will be dropped at
        # the end of login.
        request.session["sociallogin_provider"] = sociallogin.account.provider
        request.session.modified = True

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully
        connecting a social account.
        """
        assert request.user.is_authenticated
        locale = getattr(request, "LANGUAGE_CODE", None)
        return (f"/{locale}/" if locale else "/") + "settings"

    def save_user(self, request, sociallogin, form=None):
        """
        Checks for an existing user (via verified email addresses within the
        social login object) and, if one is found, associates the incoming
        social account with that existing user instead of a new user.

        It also removes the "socialaccount_sociallogin" key from the session.
        If the "socialaccount_sociallogin" key remains in the session, then the
        user will be unable to connect a second account unless they log out and
        log in again. (TODO: Check if this part of the method is still
        needed/used. I suspect not.)
        """
        # We have to call get_existing_user() again. The result of the earlier
        # call (within the is_auto_signup_allowed() method), can't be cached as
        # an attribute on the instance because a different instance of this
        # class is used when calling this method from the one used when calling
        # is_auto_signup_allowed().
        user = get_existing_user(sociallogin)
        if user:
            # We can re-use an existing user instead of creating a new one.
            # Let's guarantee this user has an unusable password, just in case
            # we're recovering an old user that has never had this done before.
            user.set_unusable_password()
            # This associates this new social account with the existing user.
            sociallogin.connect(request, user)
            # Since the "connect" call above does not add any email addresses
            # from the social login that are missing from the user's current
            # associated set, let's add them here.
            add_user_email(request, user, sociallogin.email_addresses)
            # Now that we've successfully associated a GitHub/Google social
            # account with this existing user, let's delete all of the user's
            # associated Persona social accounts (if any). Users may have
            # multiple associated Persona social accounts (each identified
            # by a unique email address).
            user.socialaccount_set.filter(provider="persona").delete()
            # Send an event to Google Analytics that the authentication
            # from one provider could be added to an account created by a
            # *different* provider (originally).
            track_event(
                CATEGORY_SIGNUP_FLOW,
                ACTION_SOCIAL_AUTH_ADD,
                f"{sociallogin.account.provider}-added",
            )
            # This is to help the 'users.user_signed_up' signal, which will
            # later kick in, to remember that we've already sent a tracking
            # event about the the "social auth add".
            request.social_auth_added = True
        else:
            user = super().save_user(request, sociallogin, form)

        try:
            del request.session["socialaccount_sociallogin"]
        except KeyError:  # pragma: no cover
            pass

        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """
        We allow "auto-signup" (basically skipping the sign-up form page) only
        if there is an existing user that we can re-use instead of creating
        a new one.
        """
        return bool(get_existing_user(sociallogin))


def get_existing_user(sociallogin):
    """
    Attempts to find an existing user that is associated with a verified email
    address that matches one of the verified email addresses within the
    "sociallogin" object.
    """
    emails = Q()
    for email_address in sociallogin.email_addresses:
        if email_address.verified:
            emails |= Q(emailaddress__email=email_address.email)
    if emails:
        # Users can have multiple associated EmailAddress objects, so
        # let's use "distinct()" to remove any duplicate users.
        users = list(
            get_user_model()
            .objects.filter(emails, emailaddress__verified=True)
            .distinct()
        )
        # For now, we're only going to return a user if there's only one.
        if len(users) == 1:
            return users[0]
    return None


def add_user_email(request, user, addresses):
    """
    This is based on allauth.account.utils.setup_user_email, but targets
    the addition of email-address objects to an existing user.
    """
    for a in cleanup_email_addresses(request, addresses)[0]:
        if not EmailAddress.objects.filter(user=user, email=a.email).exists():
            a.user = user
            a.save()
