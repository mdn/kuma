from allauth.account.auth_backends import AuthenticationBackend

from .models import UserBan


class KumaAuthBackend(AuthenticationBackend):
    """django-allauth backend, but banned users are logged out."""

    def get_user(self, user_id):
        """
        Don't allow banned users to keep logged-in session.

        This is called by django.contrib.auth, to load the user from a session
        cookie. It is called during initial login as well.
        """
        user = super(AuthenticationBackend, self).get_user(user_id)
        if user:
            bans = UserBan.objects.filter(user=user, is_active=True)
            if bans.exists():
                user = None
        return user
