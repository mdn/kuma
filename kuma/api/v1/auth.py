from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import HttpRequest
from ninja.security import HttpBearer, SessionAuth

from kuma.users.auth import KumaOIDCAuthenticationBackend, is_authorized_request
from kuma.users.models import UserProfile


class NotASubscriber(Exception):
    pass


def is_subscriber(request, raise_error=False) -> bool:
    try:
        user = request.user
        if user.is_authenticated:
            return True
        if access_token := request.META.get("HTTP_AUTHORIZATION"):
            payload = is_authorized_request(access_token)

            if error := payload.get("error"):
                raise NotASubscriber(error)

            # create user if there is not one
            request.user = KumaOIDCAuthenticationBackend.create_or_update_subscriber(
                payload
            )
            return True
        raise NotASubscriber("not a subscriber")
    except NotASubscriber:
        if raise_error:
            raise
        return False


class SubscriberAuth(SessionAuth):
    def authenticate(self, request: HttpRequest, key: str | None) -> Any:
        if is_subscriber(request):
            return request.user

        return None


subscriber_auth = SubscriberAuth()


class AdminAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> Any:
        return token == settings.NOTIFICATIONS_ADMIN_TOKEN


admin_auth = AdminAuth()


class ProfileAuth(SessionAuth):
    """
    Requires a Django authenticated user.

    Does not actually *require* a profile, but for users without a profile will
    rather return the unsaved profile ready for saving (available in
    ``request.auth``).
    """

    def authenticate(self, request: HttpRequest, key: str | None) -> Any:
        user = request.user
        if not user.is_authenticated:
            return None
        try:
            return UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return UserProfile(user=user)


profile_auth = ProfileAuth()
