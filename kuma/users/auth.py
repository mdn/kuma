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

        print("CREATE CLAIMS:")
        self._create_or_set_user_profile(user, claims)
        return user

    def update_user(self, user, claims):
        print("UPDATE CLAIMS:")
        self._create_or_set_user_profile(user, claims)
        return user

    def _create_or_set_user_profile(self, user, claims):
        (profile,) = UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "claims": claims,
            },
        )
        print("USer:", repr(user))
        print("profile=", repr(profile))
