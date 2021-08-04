import pytest

from django.test import RequestFactory

from kuma.users.auth import (
    InvalidClaimsError,
    KumaOIDCAuthenticationBackend,
    logout_url,
)
from kuma.users.models import UserProfile


@pytest.mark.django_db
def test_bark_on_no_email_claims():
    backend = KumaOIDCAuthenticationBackend()
    with pytest.raises(InvalidClaimsError):
        backend.filter_users_by_claims({})
    # Sanity check that it works when you supply an email
    qs = backend.filter_users_by_claims({"email": "peterbe@example.com"})
    assert qs.count() == 0


@pytest.mark.django_db
def test_create_and_update_user_not_subscriber():
    backend = KumaOIDCAuthenticationBackend()
    user = backend.create_user(
        {
            "email": "peterbe@example.com",
        }
    )
    assert user.email == "peterbe@example.com"
    user_profile = UserProfile.objects.get(user=user)
    assert not user_profile.is_subscriber
    assert not user_profile.subscriber_number


@pytest.mark.django_db
def test_create_and_update_user_new_subscriber():
    backend = KumaOIDCAuthenticationBackend()
    user = backend.create_user(
        {
            "email": "peterbe@example.com",
            "subscriptions": ["mdn_plus", "other_vpn_thing"],
        }
    )
    assert user.email == "peterbe@example.com"
    user_profile = UserProfile.objects.get(user=user)
    assert user_profile.is_subscriber
    assert user_profile.subscriber_number == 1

    backend.update_user(
        user,
        {
            "email": "peterbe@example.com",
            "subscriptions": ["other_vpn_thing"],  # Note!
        },
    )
    user_profile.refresh_from_db()
    assert not user_profile.is_subscriber
    assert user_profile.subscriber_number == 1


@pytest.mark.django_db
def test_update_user_from_not_to_new_subscriber():
    backend = KumaOIDCAuthenticationBackend()
    user = backend.create_user(
        {
            "email": "peterbe@example.com",
        }
    )
    assert user.email == "peterbe@example.com"
    user_profile = UserProfile.objects.get(user=user)
    assert not user_profile.is_subscriber
    assert not user_profile.subscriber_number

    backend.update_user(
        user,
        {
            "email": "peterbe@example.com",
            "subscriptions": ["mdn_plus"],  # Note!
        },
    )
    user_profile.refresh_from_db()
    assert user_profile.is_subscriber
    assert user_profile.subscriber_number == 1


def test_logout_url(settings):
    request = RequestFactory().get("/some/path")
    request.session = {}
    url = logout_url(request)
    assert url == "/"

    request = RequestFactory().get("/some/path?next=/docs")
    request.session = {}
    url = logout_url(request)
    assert url == "/docs"

    settings.LOGOUT_REDIRECT_URL = "/loggedout"
    request = RequestFactory().get("/some/path")
    request.session = {}
    url = logout_url(request)
    assert url == "/loggedout"

    request.session["oidc_login_next"] = "/original"
    url = logout_url(request)
    assert url == "/original"
