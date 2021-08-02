from django.conf import settings
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .models import UserProfile


class KumaOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        email = claims.get("email")
        if not email:
            raise NotImplementedError(
                "'email' should always be a claim. See OIDC_OP_* configuration"
            )
        return super().filter_users_by_claims(claims)

    def create_user(self, claims):
        email = claims.get("email")
        username = self.get_username(claims)
        user = self.UserModel.objects.create_user(username, email=email)

        self._create_or_set_user_profile(user, claims)
        return user

    def update_user(self, user, claims):
        self._create_or_set_user_profile(user, claims)
        return user

    def _create_or_set_user_profile(self, user, claims):
        # profile, created = UserProfile.objects.update_or_create(
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "claims": claims,
            },
        )
        # XXX Once we can use the claims stuff here to find out if they've
        # payed for MDN Plus, we can use that to forcibly set a
        # `subscriber_number` on the profile the first time we know they are
        # a paying subscriber.


def logout_url(request):
    """This gets called by mozilla_django_oidc when a user has signed out."""
    return (
        request.GET.get("next")
        or request.session.get("oidc_login_next")
        or getattr(settings, "LOGOUT_REDIRECT_URL")
        or "/"
    )
