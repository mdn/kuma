from datetime import timedelta
from unittest import mock
from urllib.parse import urlencode

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
    ACTION_PROFILE_EDIT,
    ACTION_PROFILE_EDIT_ERROR,
    ACTION_RETURNING_USER_SIGNIN,
    CATEGORY_SIGNUP_FLOW,
)
from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse

from . import create_user, SocialTestMixin, UserTestCase
from ..models import User


class KumaGitHubTests(UserTestCase, SocialTestMixin):
    def setUp(self):
        self.signup_url = reverse("socialaccount_signup")

    def test_login(self):
        resp = self.github_login()
        self.assertRedirects(resp, self.signup_url)

    def test_login_500_on_token(self):
        resp = self.github_login(token_status_code=500)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_500_on_getting_profile(self):
        resp = self.github_login(profile_status_code=500)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_500_on_getting_email_addresses(self):
        resp = self.github_login(email_status_code=500)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_SSLError_on_getting_profile(self):
        resp = self.github_login(profile_exc=SSLError)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_ProxyError_on_getting_email_addresses(self):
        resp = self.github_login(email_exc=ProxyError)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_email_addresses(self):
        public_email = "octocat-public@example.com"
        private_email = "octocat-private@example.com"
        unverified_email = "octocat-trash@example.com"
        invalid_email = "xss><svg/onload=alert(document.cookie)>@example.com"
        profile_data = self.github_profile_data.copy()
        profile_data["email"] = public_email
        email_data = [
            # It might be unrealistic but let's make sure the primary email
            # is NOT first in the list. Just to prove that pick that email not
            # on it coming first but that's the primary verified one.
            {"email": unverified_email, "verified": False, "primary": False},
            {"email": private_email, "verified": True, "primary": True},
            {"email": invalid_email, "verified": False, "primary": False},
        ]
        self.github_login(profile_data=profile_data, email_data=email_data)
        response = self.client.get(self.signup_url)
        assert response.status_code == 200
        assert_no_cache_header(response)
        doc = pq(response.content)

        # The hidden input should display the primary verified email
        assert doc.find('input[name="email"]').val() == email_data[1]["email"]
        # But whatever's in the hidden email input is always displayed to the user
        # as "plain text". Check that that also is right.
        assert doc.find("#email-static-container").text() == email_data[1]["email"]

        unverified_email = "o.ctocat@gmail.com"
        data = {
            "website": "",
            "username": "octocat",
            "email": email_data[1]["email"],
            "terms": True,
        }
        assert not EmailAddress.objects.filter(email=unverified_email).exists()
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)

        # Check that the user.email field became the primary verified one.
        user = User.objects.get(username=data["username"])
        assert user.email == email_data[1]["email"]
        assert user.emailaddress_set.count() == 1
        assert user.emailaddress_set.first().email == user.email
        assert user.emailaddress_set.first().verified
        assert user.emailaddress_set.first().primary

    def test_signup_public_github(self, is_public=True):
        resp = self.github_login()
        assert resp.redirect_chain[-1][0].endswith(self.signup_url)

        data = {
            "website": "",
            "username": "octocat",
            "email": "octocat-private@example.com",
            "terms": True,
            "is_github_url_public": is_public,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)
        user = User.objects.get(username="octocat")
        assert user.is_github_url_public == is_public

    def test_signup_private_github(self):
        self.test_signup_public_github(is_public=False)

    def test_signup_github_event_tracking(self):
        """Tests that kuma.core.ga_tracking.track_event is called when you
        sign up with GitHub for the first time."""
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
                    "website": "",
                    "username": "octocat",
                    "email": "octocat-private@example.com",
                    "terms": True,
                    "is_github_url_public": True,
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
        """Tests if a POST request comes in with an email that is NOT one of the
        options, it should reject it.
        Basically, in the sign up, you are shown what you primary default is and
        it's also in a hidden input.
        So, the only want to try to sign up with anything outside of that would
        be if you manually control the POST request or fiddle with the DOM to
        edit the hidden email input.
        """
        self.github_login()
        data = {
            "website": "",
            "username": "octocat",
            "email": "wasnot@anoption.biz",
            "terms": True,
            "is_github_url_public": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 400

    def test_signup_username_edit_event_tracking(self):
        """
        Tests that GA tracking events are sent for editing the default suggested
        username when signing-up with a new account.
        """
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.views.track_event")
            p3 = mock.patch("kuma.users.providers.google.views.track_event")
            with p1, p2 as track_event_mock_views, p3:

                response = self.google_login()

                doc = pq(response.content)
                # Just sanity check what's the defaults in the form.
                # Remember, the self.google_login relies on the provider giving an
                # email that is 'example@gmail.com'
                assert doc.find('input[name="username"]').val() == "example"
                assert doc.find('input[name="email"]').val() == "example@gmail.com"

                data = {
                    "website": "",
                    "username": "better",
                    "email": "example@gmail.com",
                    "terms": False,  # Note!
                    "is_newsletter_subscribed": True,
                }
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 200

                track_event_mock_views.assert_has_calls(
                    [
                        mock.call(CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "google"),
                        # Note the lack of 'ACTION_PROFILE_EDIT' because the form
                        # submission was invalid and the save didn't go ahead.
                    ]
                )

                # This time, the form submission will work.
                data["terms"] = True
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 302

                # Sanity check that the right user got created
                assert User.objects.get(username="better")

                track_event_mock_views.assert_has_calls(
                    [
                        mock.call(CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "google"),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_EDIT, "username edit"
                        ),
                    ]
                )

    def test_signin_github_event_tracking(self):
        """Tests that kuma.core.ga_tracking.track_event is called when you
        sign in with GitHub a consecutive time."""
        # First sign up.
        self.github_login()
        data = {
            "website": "",
            "username": "octocat",
            "email": "octocat-private@example.com",
            "terms": True,
            "is_github_url_public": True,
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
        response = self.google_login()
        assert response.status_code == 200

        doc = pq(response.content)
        # The default suggested username should be the `email.split('@')[0]`
        email = self.google_profile_data["email"]
        username = email.split("@")[0]
        assert doc.find('input[name="username"]').val() == username
        # first remove the button from that container
        doc("#username-static-container button").remove()
        # so that what's left is just the username
        assert doc.find("#username-static-container").text() == username

        # The hidden input should display the primary verified email
        assert doc.find('input[name="email"]').val() == email
        # But whatever's in the hidden email input is always displayed to the user
        # as "plain text". Check that that also is right.
        assert doc.find("#email-static-container").text() == email

        data = {
            "website": "",  # for the honeypot
            "username": username,
            "email": email,
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
        """When you load the signup form, our backend recognizes what your valid
        email address can be. But what if someone changes the hidden input to
        something other that what's there by default. That should get kicked out.
        """
        self.google_login()
        email = self.google_profile_data["email"]
        username = email.split("@")[0]

        data = {
            "website": "",  # for the honeypot
            "username": username,
            "email": "somethingelse@example.biz",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 400

    def test_clashing_username(self):
        """First a GitHub user exists. Then a Google user tries to sign up
        whose email address, when `email.split('@')[0]` would become the same
        as the existing GitHub user.
        """
        create_user(username="octocat", save=True)
        self.google_login(
            profile_data=dict(
                self.google_profile_data,
                email="octocat@gmail.com",
            )
        )
        response = self.client.get(self.signup_url)
        assert response.status_code == 200
        doc = pq(response.content)
        assert doc.find('input[name="username"]').val() == "octocat2"

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
                    "website": "",
                    "username": "octocat",
                    "email": "octocat-private@example.com",
                    "terms": True,
                    "is_newsletter_subscribed": True,
                }
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 200

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


def test_signin_landing(db, client, settings):
    response = client.get(f"/en-US{settings.LOGIN_URL}")
    github_login_url = "/users/github/login/"
    google_login_url = "/users/google/login/"
    # first, make sure that the page loads
    assert response.status_code == 200
    doc = pq(response.content)
    # ensure that both auth buttons are present
    assert doc(".auth-button-container a").length == 2
    # ensure each button links to the appropriate endpoint
    assert doc(".github-auth").attr.href == github_login_url
    assert doc(".google-auth").attr.href == google_login_url
    # just to be absolutely clear, there is no ?next=... on *this* page
    assert "next" not in doc(".github-auth").attr.href
    assert "next" not in doc(".google-auth").attr.href


def test_signin_landing_next(db, client, settings):
    """Going to /en-US/users/account/signup-landing?next=THIS should pick put
    that 'THIS' and put it into the Google and GitHub auth links."""
    next_page = "/en-US/Foo/Bar"
    response = client.get(f"/en-US{settings.LOGIN_URL}", {"next": next_page})
    assert response.status_code == 200
    doc = pq(response.content)
    github_login_url = "/users/github/login/"
    google_login_url = "/users/google/login/"
    next = f"?{urlencode({'next': next_page})}"
    assert doc(".github-auth").attr.href == github_login_url + next
    assert doc(".google-auth").attr.href == google_login_url + next
