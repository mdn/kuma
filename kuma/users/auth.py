from django.conf import settings
from django.db.models import Max
from django.utils import timezone
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .models import UserProfile


class InvalidClaimsError(ValueError):
    """When the claims are bonkers"""


def get_next_subscriber_number():
    max_subscriber_number = UserProfile.objects.filter(
        subscriber_number__isnull=False
    ).aggregate(max_subscriber_number=Max("subscriber_number"))["max_subscriber_number"]
    # The absolute very first time you do this aggregate it
    # will become None because there's 0 rows to aggregate on.
    # That's why we do this `max_subscriber_number or 0`.
    return (max_subscriber_number or 0) + 1


class KumaOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        """
        Fail authentication if the user is not an MDN Plus subscriber.
        """
        subscriptions = claims.get("subscriptions")
        return subscriptions and "mdn_plus" in subscriptions

    def filter_users_by_claims(self, claims):
        email = claims.get("email")
        if not email:
            raise InvalidClaimsError(
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
        subscriptions = claims.get("subscriptions")
        is_subscriber = (
            timezone.now() if subscriptions and "mdn_plus" in subscriptions else None
        )
        for user_profile in UserProfile.objects.filter(user=user):
            user_profile.claims = claims
            if not user_profile.is_subscriber and is_subscriber:
                # Welcome to being a new subscriber!
                user_profile.subscriber_number = get_next_subscriber_number()
            user_profile.is_subscriber = is_subscriber
            user_profile.save()
            break
        else:
            subscriber_number = get_next_subscriber_number() if is_subscriber else None
            UserProfile.objects.create(
                user=user,
                claims=claims,
                is_subscriber=is_subscriber,
                subscriber_number=subscriber_number,
            )


def logout_url(request):
    """This gets called by mozilla_django_oidc when a user has signed out."""
    return (
        request.GET.get("next")
        or request.session.get("oidc_login_next")
        or getattr(settings, "LOGOUT_REDIRECT_URL", None)
        or "/"
    )
