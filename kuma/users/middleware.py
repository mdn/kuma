import time

from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import MiddlewareNotUsed
from mozilla_django_oidc.middleware import SessionRefresh

from kuma.users.auth import KumaOIDCAuthenticationBackend


class ValidateAccessTokenMiddleware(SessionRefresh):
    """Validate the access token every hour.

    Verify that the access token has not been invalidated
    by the user through the Firefox Accounts web interface.
    """

    def __init__(self, *args, **kwargs):
        if settings.DEV and settings.DEBUG:
            raise MiddlewareNotUsed
        super().__init__(*args, **kwargs)

    def process_request(self, request):

        if not self.is_refreshable_url(request):
            return

        expiration = request.session.get("oidc_id_token_expiration", 0)
        now = time.time()
        access_token = request.session.get("oidc_access_token")
        profile = request.user.userprofile

        if access_token and expiration < now:

            token_info = KumaOIDCAuthenticationBackend.refresh_access_token(
                profile.fxa_refresh_token
            )
            new_access_token = token_info.get("access_token")
            if new_access_token:
                request.session["oidc_access_token"] = new_access_token
                request.session["oidc_id_token_expiration"] = (
                    now + settings.FXA_TOKEN_EXPIRY
                )
            else:
                profile.fxa_refresh_token = ""
                profile.save()
                logout(request)
