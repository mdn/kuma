from datetime import timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from pyquery import PyQuery as pq
from requests.exceptions import ProxyError, SSLError

from kuma.core.ga_tracking import (
    ACTION_AUTH_STARTED,
    ACTION_AUTH_SUCCESSFUL,
    ACTION_FREE_NEWSLETTER,
    ACTION_PROFILE_AUDIT,
    ACTION_PROFILE_CREATED,
    ACTION_PROFILE_EDIT_ERROR,
    ACTION_RETURNING_USER_SIGNIN,
    CATEGORY_SIGNUP_FLOW,
)
from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse

from . import create_user, SocialTestMixin, UserTestCase
from ..models import User


def mock_reverse(viewname, **kwargs):
    """
    Mock reverse function for the error-handling tests, since these
    "views" don't exist in Kuma. They are provided by Yari.
    """
    if viewname == "account_signup":
        return "/en-US/signup"
    elif viewname == "account_login":
        return "/en-US/signin"
    raise Exception(f"unknown endpoint: {viewname}")


class KumaGitHubTests(UserTestCase, SocialTestMixin):
    def setUp(self):
        self.signup_url = reverse("socialaccount_signup")

    def test_login(self):
        """
        We're testing that the GitHub login process eventually redirects
        to the Yari signup page, passing along public information via the
        query string.
        """
        resp = self.github_login()
        assert hasattr(resp, "redirect_chain")
        signup_url = urlparse(resp.redirect_chain[-1][0])
        assert signup_url.path == "/en-US/signup"
        query = parse_qs(signup_url.query)
        assert query["next"][0] == "None"
        assert query["provider"][0] == "github"
        user_details = query["user_details"][0]
        assert f'"name": "{self.github_profile_data["name"]}"' in user_details
        assert (
            f'"avatar_url": "{self.github_profile_data["avatar_url"]}"' in user_details
        )
        assert "csrfmiddlewaretoken" in query
        assert resp.redirect_chain[-1][1] == 302

        data = {
            "locale": "en-US",
            "next": "/en-US/",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)
        user = User.objects.get(username="octocat")
        assert user.email == self.github_profile_data["email"]

    def test_login_500_on_token(self):
        # TODO: We're simply testing here that the error is acknowledged properly.
        # We need to work on a different way to handle these errors so they can be
        # displayed on our Yari-built signin page "/{locale}/signin".
        with mock.patch("django.urls.reverse", side_effect=mock_reverse):
            resp = self.github_login(token_status_code=500)
            assert resp.status_code == 200
            assert pq(resp.content).find("h1").text() == "Social Network Login Failure"

    def test_login_500_on_getting_profile(self):
        with mock.patch("django.urls.reverse", side_effect=mock_reverse):
            resp = self.github_login(profile_status_code=500)
            assert resp.status_code == 200
            assert pq(resp.content).find("h1").text() == "Social Network Login Failure"

    def test_login_500_on_getting_email_addresses(self):
        with mock.patch("django.urls.reverse", side_effect=mock_reverse):
            resp = self.github_login(email_status_code=500)
            assert resp.status_code == 200
            assert pq(resp.content).find("h1").text() == "Social Network Login Failure"

    def test_login_SSLError_on_getting_profile(self):
        with mock.patch("django.urls.reverse", side_effect=mock_reverse):
            resp = self.github_login(profile_exc=SSLError)
            assert resp.status_code == 200
            assert pq(resp.content).find("h1").text() == "Social Network Login Failure"

    def test_login_ProxyError_on_getting_email_addresses(self):
        with mock.patch("django.urls.reverse", side_effect=mock_reverse):
            resp = self.github_login(email_exc=ProxyError)
            assert resp.status_code == 200
            assert pq(resp.content).find("h1").text() == "Social Network Login Failure"

    def test_email_addresses(self):
        public_email = "octocat-public@example.com"
        private_email = "octocat-private@example.com"
        unverified_email = "octocat-trash@example.com"
        invalid_email = "xss><svg/onload=alert(document.cookie)>@example.com"
        profile_data = self.github_profile_data.copy()
        profile_data["email"] = public_email
        email_data = [
            # It might be unrealistic but let's make sure the primary email is
            # NOT first in the list. Just to prove that email is picked because
            # it's the primary verified one, not because it's first in the list.
            {"email": unverified_email, "verified": False, "primary": False},
            {"email": private_email, "verified": True, "primary": True},
            {"email": invalid_email, "verified": False, "primary": False},
        ]
        self.github_login(profile_data=profile_data, email_data=email_data)

        unverified_email = "o.ctocat@gmail.com"
        data = {
            "locale": "en-US",
            "next": "/en-US/",
            "email": email_data[1]["email"],
            "terms": True,
        }
        assert not EmailAddress.objects.filter(email=unverified_email).exists()
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)

        # Check that the user.email field became the primary verified one.
        user = User.objects.get(username="octocat")
        assert user.email == email_data[1]["email"]
        assert user.emailaddress_set.count() == 1
        assert user.emailaddress_set.first().email == user.email
        assert user.emailaddress_set.first().verified
        assert user.emailaddress_set.first().primary

    def test_signup_github_event_tracking(self):
        """
        Tests that kuma.core.ga_tracking.track_event is called when you
        sign up with GitHub for the first time.
        """
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.views.track_event")
            p3 = mock.patch("kuma.users.providers.github.views.track_event")
            with p1 as track_event_mock_signals, p2 as track_event_mock_views, p3 as track_event_mock_github:

                self.github_login(
                    headers={
                        # Needed to trigger the 'auth-started' GA tracking event.
                        "HTTP_REFERER": "http://testserver/en-US/"
                    }
                )

                data = {
                    "locale": "en-US",
                    "next": "/en-US/",
                    "terms": True,
                }
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 302
                assert User.objects.get(username="octocat")

                track_event_mock_signals.assert_has_calls(
                    [
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_AUTH_SUCCESSFUL, "github"
                        ),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_CREATED, "github"
                        ),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_FREE_NEWSLETTER, "opt-out"
                        ),
                    ]
                )
                track_event_mock_github.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, "github"
                )

                track_event_mock_views.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "github"
                )

    def test_signup_github_email_manual_override(self):
        """
        Tests if a POST request comes in with an email that is NOT one of the
        options, it should reject it.
        """
        self.github_login()
        data = {
            "email": "wasnot@anoption.biz",
            "locale": "en-US",
            "next": "/en-US/",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 400

    def test_signin_github_event_tracking(self):
        """Tests that kuma.core.ga_tracking.track_event is called when you
        sign in with GitHub a consecutive time."""
        # First sign up.
        self.github_login()
        data = {
            "locale": "en-US",
            "next": "/en-US/",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        user = User.objects.get(username="octocat")

        # Pretend that some time goes by
        user.date_joined -= timedelta(minutes=1)
        user.save()

        # Now, this time sign in.
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            # This syntax looks a bit weird but it's just to avoid having
            # to write all mock patches on one super long line in the
            # 'with' statement.
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.providers.github.views.track_event")
            with p1 as track_event_mock_signals, p2 as track_event_mock_github:
                response = self.github_login(
                    follow=False,
                    # Needed to trigger the 'auth-started' GA tracking event.
                    headers={"HTTP_REFERER": "http://testserver/en-US/"},
                )
                assert response.status_code == 302

                track_event_mock_signals.assert_has_calls(
                    [
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_AUTH_SUCCESSFUL, "github"
                        ),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_RETURNING_USER_SIGNIN, "github"
                        ),
                    ]
                )
                track_event_mock_github.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, "github"
                )

    def test_account_tokens(self):
        testemail = "account_token@acme.com"
        testuser = create_user(
            username="user", is_active=True, email=testemail, password="test", save=True
        )
        EmailAddress.objects.create(
            user=testuser, email=testemail, primary=True, verified=True
        )
        self.client.login(username=testuser.username, password="test")

        token = "access_token"
        refresh_token = "refresh_token"
        token_data = self.github_token_data.copy()
        token_data["access_token"] = token
        token_data["refresh_token"] = refresh_token

        self.github_login(token_data=token_data, process="connect")
        social_account = SocialAccount.objects.get(user=testuser, provider="github")
        social_token = social_account.socialtoken_set.get()
        assert token == social_token.token
        assert refresh_token == social_token.token_secret

    def test_account_refresh_token_saved_next_login(self):
        """
        fails if a login missing a refresh token, deletes the previously
        saved refresh token. Systems such as google's oauth only send
        a refresh token on first login.
        """
        # Setup a user with a token and refresh token
        testemail = "account_token@acme.com"
        testuser = create_user(
            username="user", is_active=True, email=testemail, password="test", save=True
        )
        EmailAddress.objects.create(
            user=testuser, email=testemail, primary=True, verified=True
        )
        token = "access_token"
        refresh_token = "refresh_token"
        app = self.ensure_github_app()
        sa = testuser.socialaccount_set.create(provider=app.provider)
        sa.socialtoken_set.create(app=app, token=token, token_secret=refresh_token)

        # Login without a refresh token
        token_data = self.github_token_data.copy()
        token_data["access_token"] = token
        self.github_login(token_data=token_data, process="login")

        # Refresh token is still in database
        sa.refresh_from_db()
        social_token = sa.socialtoken_set.get()
        assert token == social_token.token
        assert refresh_token == social_token.token_secret


class KumaGoogleTests(UserTestCase, SocialTestMixin):
    def setUp(self):
        self.signup_url = reverse("socialaccount_signup")

    def test_signup_google(self):
        """
        We're testing that the Google login process eventually redirects
        to the Yari signup page, passing along public information via the
        query string.
        """
        resp = self.google_login()
        assert hasattr(resp, "redirect_chain")
        signup_url = urlparse(resp.redirect_chain[-1][0])
        assert signup_url.path == "/en-US/signup"
        query = parse_qs(signup_url.query)
        assert query["next"][0] == "None"
        assert query["provider"][0] == "google"
        user_details = query["user_details"][0]
        print(f"user_details = {user_details}")
        assert f'"name": "{self.google_profile_data["name"]}"' in user_details
        assert f'"avatar_url": "{self.google_profile_data["picture"]}"' in user_details
        assert "csrfmiddlewaretoken" in query
        assert resp.redirect_chain[-1][1] == 302

        email = self.google_profile_data["email"]
        username = email.split("@")[0]
        data = {
            "locale": "en-US",
            "next": "/en-US/",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)

        user = User.objects.get(username=username)
        assert user.email == email

        assert EmailAddress.objects.filter(
            email=email, primary=True, verified=True
        ).exists()

    def test_signup_google_changed_email(self):
        """
        Reject an invalid email address.
        """
        self.google_login()
        data = {
            "email": "somethingelse@example.biz",
            "locale": "en-US",
            "next": "/en-US/",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 400

    def test_clashing_username(self):
        """
        First a GitHub user exists. Then a Google user tries to sign up
        whose email address (`email.split('@')[0]`) would become the same
        as the existing GitHub user.
        """
        create_user(username="example", save=True)
        self.google_login()
        data = {
            "locale": "en-US",
            "next": "/en-US/",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)

        user = User.objects.get(username="example")
        assert not user.email

        user = User.objects.get(username="example2")
        assert user.email == self.google_profile_data["email"]

        assert EmailAddress.objects.filter(
            email=self.google_profile_data["email"], primary=True, verified=True
        ).exists()

    def test_signup_username_error_event_tracking(self):
        """
        Tests that GA tracking events are sent for errors in the username
        field submitted when signing-up with a new account.
        """
        create_user(username="octocat", save=True)
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.views.track_event")
            p3 = mock.patch("kuma.users.providers.google.views.track_event")
            with p1 as track_event_mock_signals, p2 as track_event_mock_views, p3 as track_event_mock_google:

                self.google_login(
                    headers={
                        # Needed to trigger the 'auth-started' GA tracking event.
                        "HTTP_REFERER": "http://testserver/en-US/"
                    }
                )

                data = {
                    "username": "octocat",
                    "locale": "en-US",
                    "next": "/en-US/",
                    "terms": True,
                }
                self.client.post(self.signup_url, data=data)

                track_event_mock_signals.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_SUCCESSFUL, "google"
                )
                track_event_mock_google.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, "google"
                )
                track_event_mock_views.assert_has_calls(
                    [
                        mock.call(CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "google"),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_EDIT_ERROR, "username"
                        ),
                    ]
                )
