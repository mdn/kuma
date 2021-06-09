from unittest import mock

import pytest
from allauth.account.models import EmailAddress
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from kuma.core.ga_tracking import ACTION_SOCIAL_AUTH_ADD, CATEGORY_SIGNUP_FLOW
from kuma.users.adapters import KumaSocialAccountAdapter
from kuma.users.models import User

from . import UserTestCase


class KumaSocialAccountAdapterTestCase(UserTestCase):
    rf = RequestFactory()

    def setUp(self):
        """ extra setUp to make a working session """
        super(KumaSocialAccountAdapterTestCase, self).setUp()
        self.adapter = KumaSocialAccountAdapter()

    def test_pre_social_login_overwrites_session_var(self):
        """
        When a user logs in a second time, second login wins the session.

        https://bugzil.la/1055870
        """
        # Set up a pre-existing "Alternate" sign-in session
        request = self.rf.get("/")
        session = self.client.session
        session["sociallogin_provider"] = "alternate"
        session.save()
        request.session = session

        # Set up a in-process GitHub SocialLogin (unsaved)
        account = SocialAccount.objects.get(user__username="testuser")
        assert account.provider == "github"
        sociallogin = SocialLogin(account=account)

        # Verify the social_login receiver over-writes the provider
        # stored in the session
        self.adapter.pre_social_login(request, sociallogin)
        assert account.provider == request.session["sociallogin_provider"]

    def test_pre_social_login_error_for_unmatched_login(self):
        """
        When we suspect the signup form is used as a connection form, abort.

        https://bugzil.la/1063830
        """
        # Set up a GitHub SocialLogin in the session
        github_account = SocialAccount.objects.get(user__username="testuser2")
        github_login = SocialLogin(account=github_account, user=github_account.user)

        request = self.rf.get("/")
        session = self.client.session
        session["socialaccount_sociallogin"] = github_login.serialize()
        session.save()
        request.session = session

        # Set up an un-matching alternate SocialLogin for request
        other_account = SocialAccount(
            user=self.user_model(), provider="other", uid="noone@inexistant.com"
        )
        other_login = SocialLogin(account=other_account)

        self.assertRaises(
            ImmediateHttpResponse, self.adapter.pre_social_login, request, other_login
        )

    def test_pre_social_login_matched_github_login(self):
        """
        When we detected a legacy Persona account, advise recovery of account.

        A user tries to sign in with GitHub, but their GitHub email matches
        an existing MDN account backed by Persona. They are prompted to
        recover the existing account.

        https://bugzil.la/1063830, happy path
        """
        # Set up a session-only GitHub SocialLogin
        # These are created at the start of the signup process, and saved on
        #  profile completion.
        github_account = SocialAccount.objects.get(user__username="testuser2")
        github_login = SocialLogin(account=github_account, user=github_account.user)

        # Setup existing Persona SocialLogin for the same email
        SocialAccount.objects.create(
            user=github_account.user, provider="persona", uid=github_account.user.email
        )

        request = self.rf.get("/")
        session = self.client.session
        session["sociallogin_provider"] = "github"
        session["socialaccount_sociallogin"] = github_login.serialize()
        session.save()
        request.session = session

        # Verify the social_login receiver over-writes the provider
        # stored in the session
        self.adapter.pre_social_login(request, github_login)
        session = request.session
        assert "github" == session["sociallogin_provider"]

    def test_pre_social_login_matched_google_login(self):
        """
        When we detected a legacy Persona account, advise recovery of account.

        A user tries to sign in with Google, but their Google email matches
        an existing MDN account backed by Persona. They are prompted to
        recover the existing account.

        Same as above, but with Google instead of GitHub
        """
        # Set up a session-only Google SocialLogin
        # These are created at the start of the signup process, and saved on
        #  profile completion.
        google_account = SocialAccount.objects.get(user__username="gogol")
        google_login = SocialLogin(account=google_account, user=google_account.user)

        # Setup existing Persona SocialLogin for the same email
        SocialAccount.objects.create(
            user=google_account.user, provider="persona", uid=google_account.user.email
        )

        request = self.rf.get("/")
        session = self.client.session
        session["sociallogin_provider"] = "google"
        session["socialaccount_sociallogin"] = google_login.serialize()
        session.save()
        request.session = session

        # Verify the social_login receiver over-writes the provider
        # stored in the session
        self.adapter.pre_social_login(request, google_login)
        session = request.session
        assert "google" == session["sociallogin_provider"]

    def test_pre_social_login_same_provider(self):
        """
        pre_social_login passes if existing provider is the same.

        I'm not sure what the real-world counterpart of this is. Logging
        in with a different GitHub account? Needed for branch coverage.
        """

        # Set up a GitHub SocialLogin in the session
        github_account = SocialAccount.objects.get(user__username="testuser2")
        github_login = SocialLogin(account=github_account, user=github_account.user)

        request = self.rf.get("/")
        session = self.client.session
        session["sociallogin_provider"] = "github"
        session["socialaccount_sociallogin"] = github_login.serialize()
        session.save()
        request.session = session

        # Set up an un-matching GitHub SocialLogin for request
        github2_account = SocialAccount(
            user=self.user_model(), provider="github", uid=github_account.uid + "2"
        )
        github2_login = SocialLogin(account=github2_account)

        self.adapter.pre_social_login(request, github2_login)
        assert "github" == request.session["sociallogin_provider"]


@pytest.mark.parametrize("provider", ("github", "google"))
@pytest.mark.parametrize(
    "case",
    (
        "match",
        "nomatch_address",
        "nomatch_user_unverified",
        "nomatch_social_unverified",
    ),
)
def test_user_reuse_on_social_login(wiki_user, client, rf, case, provider):
    """
    Test all cases related to re-using an existing user on social login.
    """
    # Make explicit the assumption that the social-login provider which we're
    # signing-up with is not yet associated with the existing user.
    wiki_user_social_account = SocialAccount.objects.filter(
        user=wiki_user, provider=provider
    )
    assert not wiki_user_social_account.exists()

    # Let's give the user a usable password so we can check later if that's
    # been remedied if we find a match.
    wiki_user.set_password("qwerty")
    wiki_user.save()

    social_email_address = (
        "user@nomatch.com" if case == "nomatch_address" else wiki_user.email
    )
    user_email_verified = case != "nomatch_user_unverified"
    social_email_verified = case != "nomatch_social_unverified"

    primary_social_email = {
        "email": social_email_address,
        "primary": True,
        "verified": social_email_verified,
        "visibility": "public",
    }
    extra_social_email = {
        "email": "user@junk.com",
        "primary": False,
        "verified": False,
        "visibility": None,
    }
    social_emails = [primary_social_email, extra_social_email]

    if provider == "github":
        other_provider = "google"
        social_login = SocialLogin(
            user=User(username="new_user"),
            account=SocialAccount(
                uid=1234567,
                provider="github",
                extra_data={
                    "email": None,
                    "login": "new_user",
                    "name": "Paul McCartney",
                    "avatar_url": "https://yada/yada",
                    "html_url": "https://github.com/new_user",
                    "email_addresses": social_emails,
                },
            ),
            email_addresses=[
                EmailAddress(
                    email=a["email"], verified=a["verified"], primary=a["primary"]
                )
                for a in social_emails
            ],
        )
    else:
        other_provider = "github"
        social_login = SocialLogin(
            user=User(username="new_user"),
            account=SocialAccount(
                uid=123456789012345678901,
                provider="google",
                extra_data={
                    "email": primary_social_email["email"],
                    "verified_email": primary_social_email["verified"],
                    "name": "Paul McCartney",
                    "given_name": "Paul",
                    "family_name": "McCartney",
                    "picture": "https://yada/yada",
                },
            ),
            email_addresses=[
                EmailAddress(
                    email=primary_social_email["email"],
                    verified=primary_social_email["verified"],
                    primary=primary_social_email["primary"],
                )
            ],
        )

    # Associate social accounts with the wiki_user other than the social-login
    # provider we're signing-up with.
    for prov in ("persona", other_provider):
        SocialAccount.objects.create(user=wiki_user, provider=prov)
    # Associate an email address with the wiki_user.
    EmailAddress.objects.create(
        user=wiki_user, email=wiki_user.email, verified=user_email_verified
    )

    request = rf.get(f"/users/{provider}/login")
    request.user = AnonymousUser()
    request.session = client.session

    # Run through the same steps that django-allauth takes after the OAuth2
    # dance has completed. Doing it this way avoids having to mock the entire
    # OAuth2 dance.
    response = complete_social_login(request, social_login)

    # The response should be an instance of HttpResponseRedirect.
    assert response.status_code == 302
    # If we found a matching user, we should have been logged-in without
    # any further steps, and redirected to the home page. Otherwise we should
    # have been redirected to the account-signup page to continue the process.
    assert response.url == ("/" if case == "match" else "/en-US/users/account/signup")
    # The wiki_user's password should have been made unusable but only if we
    # found a match.
    wiki_user.refresh_from_db()
    assert wiki_user.has_usable_password() == (case != "match")

    # A new GitHub social account should have been associated with the existing
    # wiki_user only if we found a match.
    assert wiki_user_social_account.exists() == (case == "match")
    if provider == "github":
        # The extra social-login email address not yet associated with the
        # existing wiki_user should have been created only if we found a match.
        assert (
            EmailAddress.objects.filter(
                user=wiki_user,
                email=extra_social_email["email"],
                verified=extra_social_email["verified"],
            ).exists()
        ) == (case == "match")
    # The associated Persona social account should have been deleted only if
    # we found a match.
    assert (
        SocialAccount.objects.filter(user=wiki_user, provider="persona").exists()
    ) == (case != "match")


@pytest.fixture
def mock_track_event():
    mock1 = mock.patch("kuma.users.adapters.track_event")
    mock2 = mock.patch("kuma.users.signal_handlers.track_event")
    with mock1 as func, mock2:
        yield func


def test_ga_tracking_reuse_social_login(
    settings, client, wiki_user, rf, mock_track_event
):
    """Specifically triggering the GA tracking when it reuses a social login.

    This test is a condensed and not commented version of
    test_user_reuse_on_social_login() above but with the specific case of
    a user with a verified Google account this time logged in using GitHub.

    The most important thing is to test that the track_event() function is
    called.
    """
    provider = "github"
    # When this is set, track_event() will do things.
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    # This unhides potential errors that should otherwise be swallowed
    # in regular production use.
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = True

    wiki_user_social_account = SocialAccount.objects.filter(
        user=wiki_user, provider=provider
    )
    assert not wiki_user_social_account.exists()
    wiki_user.set_password("qwerty")
    wiki_user.save()

    # social_email_address = wiki_user.email
    user_email_verified = True
    primary_social_email = {
        "email": wiki_user.email,
        "primary": True,
        "verified": user_email_verified,
        "visibility": "public",
    }
    extra_social_email = {
        "email": "user@junk.com",
        "primary": False,
        "verified": False,
        "visibility": None,
    }
    social_emails = [primary_social_email, extra_social_email]

    social_login = SocialLogin(
        user=User(username="new_user"),
        account=SocialAccount(
            uid=1234567,
            provider="github",
            extra_data={
                "email": None,
                "login": "new_user",
                "name": "Paul McCartney",
                "avatar_url": "https://yada/yada",
                "html_url": "https://github.com/new_user",
                "email_addresses": social_emails,
            },
        ),
        email_addresses=[
            EmailAddress(email=a["email"], verified=a["verified"], primary=a["primary"])
            for a in social_emails
        ],
    )
    EmailAddress.objects.create(
        user=wiki_user, email=wiki_user.email, verified=user_email_verified
    )
    request = rf.get(f"/users/{provider}/login")
    request.user = AnonymousUser()
    request.session = client.session

    response = complete_social_login(request, social_login)
    assert response.status_code == 302
    assert response.url == "/"

    mock_track_event.assert_called_with(
        CATEGORY_SIGNUP_FLOW, ACTION_SOCIAL_AUTH_ADD, "github-added"
    )
