import time

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .models import UserProfile


class KumaOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """Extend mozilla-django-oidc authbackend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh_token = None

    def get_token(self, payload):
        """Override get_token to extract the refresh token."""
        token_info = super().get_token(payload)
        self.refresh_token = token_info.get("refresh_token")
        return token_info

    @classmethod
    def refresh_access_token(cls, refresh_token, ttl=None):
        """Gets a new access_token by using a refresh_token.

        returns: the actual token or an empty dictionary
        """

        if not refresh_token:
            return {}

        obj = cls()
        payload = {
            "client_id": obj.OIDC_RP_CLIENT_ID,
            "client_secret": obj.OIDC_RP_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        if ttl:
            payload.update({"ttl": ttl})

        try:
            return obj.get_token(payload=payload)
        except requests.exceptions.HTTPError:
            return {}

    def filter_users_by_claims(self, claims):
        user_model = get_user_model()

        if not (fxa_uid := claims.get("sub")):
            return user_model.objects.none()

        return user_model.objects.filter(username=fxa_uid)

    def create_user(self, claims):
        user = super().create_user(claims)

        self._create_or_set_user_profile(user, claims)
        self.request.created = True
        return user

    def update_user(self, user, claims):
        self._create_or_set_user_profile(user, claims)
        return user

    def get_username(self, claims):
        """Get the username from the claims."""
        # use the fxa_uid as the username
        return claims.get("sub", claims.get("uid"))

    @staticmethod
    def create_or_update_subscriber(claims, user=None):
        """Retrieve or create a user with a profile.

        Static helper method that routes requests that are not part of the login flow
        """
        email = claims.get("email")
        fxa_uid = claims.get("sub", claims.get("uid"))
        if not fxa_uid:
            return

        try:
            # short-circuit if we already have a user
            user = user or get_user_model().objects.get(username=fxa_uid)
        except get_user_model().DoesNotExist:
            user = get_user_model().objects.create_user(email=email, username=fxa_uid)

        # update the email if needed
        if email and user.email != email:
            user.email = email
        # toggle user status based on subscriptions
        user.is_active = True
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if avatar := claims.get("avatar"):
            profile.avatar = avatar

        profile.is_subscriber = settings.MDN_PLUS_SUBSCRIPTION in claims.get(
            "subscriptions", []
        ) or settings.MDN_PLUS_SUBSCRIPTION == claims.get("fxa-subscriptions", "")
        profile.save()

        return user

    def _create_or_set_user_profile(self, user, claims):
        """Update user and profile attributes."""
        user = self.create_or_update_subscriber(claims, user)

        if self.refresh_token:
            UserProfile.objects.filter(user=user).update(
                fxa_refresh_token=self.refresh_token
            )


def logout_url(request):
    """This gets called by mozilla_django_oidc when a user has signed out."""
    return (
        request.GET.get("next")
        or request.session.get("oidc_login_next")
        or getattr(settings, "LOGOUT_REDIRECT_URL", None)
        or "/"
    )


def is_authorized_request(token, **kwargs):

    auth = token.split()
    if auth[0].lower() != "bearer":
        return {"error": "invalid token type"}

    jwt_token = auth[1]
    if not (payload := KumaOIDCAuthenticationBackend().verify_token(jwt_token)):
        return {"error": "invalid token"}

    issuer = payload["iss"]
    exp = payload["exp"]

    # # If the issuer is not Firefox Accounts log an error
    if settings.FXA_TOKEN_ISSUER != issuer:
        return {"error": "invalid token issuer"}

    # Check if the token is expired
    if exp < time.time():
        return {"error": "token expired"}

    return payload
