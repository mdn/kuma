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

    def filter_users_by_claims(self, claims):
        user_model = get_user_model()

        if not (fxa_uid := claims.get("uid")):
            return user_model.objects.none()

        return user_model.objects.filter(
            userprofile__fxa_uid=fxa_uid
        ) or super().filter_users_by_claims(claims)

    def create_user(self, claims):
        if (
            not (subscriptions := claims.get("subscriptions"))
            or settings.MDN_PLUS_SUBSCRIPTION not in subscriptions
        ):
            return None
        user = super().create_user(claims)

        self._create_or_set_user_profile(user, claims)
        return user

    def update_user(self, user, claims):
        self._create_or_set_user_profile(user, claims)
        return user

    def _create_or_set_user_profile(self, user, claims):
        """Update user and profile attributes."""
        email = claims.get("email")

        # update the email if needed
        if email and user.email != email:
            user.email = email
        # toggle user status based on subscriptions
        user.is_active = settings.MDN_PLUS_SUBSCRIPTION in claims.get(
            "subscriptions", []
        )
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.avatar = claims.get("avatar")
        profile.fxa_uid = claims.get("uid")

        if self.refresh_token:
            profile.fxa_refresh_token = self.refresh_token
        profile.save()


def logout_url(request):
    """This gets called by mozilla_django_oidc when a user has signed out."""
    return (
        request.GET.get("next")
        or request.session.get("oidc_login_next")
        or getattr(settings, "LOGOUT_REDIRECT_URL", None)
        or "/"
    )
