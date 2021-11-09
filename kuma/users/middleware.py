import time

import requests
from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import MiddlewareNotUsed
from mozilla_django_oidc.middleware import SessionRefresh


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

        if access_token and expiration < now:

            response_token_info = (
                requests.post(settings.FXA_VERIFY_URL, data={"token": access_token})
            ).json()

            # if the token is not verified, log the user out
            if (
                response_token_info.get("code") == 400
                and response_token_info.get("message") == "Invalid token"
            ):
                logout(request)
            else:
                request.session["oidc_id_token_expiration"] = (
                    now + settings.FXA_TOKEN_EXPIRY
                )
