import json

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from josepy.jwk import JWK
from josepy.jws import JWS
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)

from kuma.users.models import AccountEvent, UserProfile
from kuma.users.tasks import (
    process_event_delete_user,
    process_event_password_change,
    process_event_profile_change,
    process_event_subscription_state_change,
)


class NoPromptOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    def get_extra_params(self, request):
        params = {"next": "/en-US/plus"}
        email = request.GET.get("email")
        if email:
            # Note that "prompt=none" will fail if "login_hint"
            # is not also provided with the user's correct email.
            params.update(prompt="none", login_hint=email)
        return params


no_prompt_login = NoPromptOIDCAuthenticationRequestView.as_view()


class KumaOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    @property
    def success_url(self):
        try:
            profile = UserProfile.objects.get(user=self.user)
            is_subscriber = profile.is_subscriber
        except UserProfile.DoesNotExist:
            is_subscriber = False

        # Redirect new users to Plus.
        if (
            hasattr(self.request, "created")
            and self.request.created
            and not is_subscriber
        ):
            return "/en-US/plus"
        return super().success_url


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    """The flow here is based on the mozilla-django-oidc lib.

    If/When the said lib supports SET tokens this will be replaced by the lib.
    """

    def retrieve_matching_jwk(self, header):
        """Get the signing key by exploring the JWKS endpoint of the OP."""

        response_jwks = requests.get(
            settings.OIDC_OP_JWKS_ENDPOINT,
        )
        response_jwks.raise_for_status()
        jwks = response_jwks.json()

        key = None
        for jwk in jwks["keys"]:
            if jwk["kid"] != header.get("kid"):
                continue
            if "alg" in jwk and jwk["alg"] != header["alg"]:
                raise SuspiciousOperation("alg values do not match.")
            key = jwk
        if key is None:
            raise SuspiciousOperation("Could not find a valid JWKS.")
        return key

    def verify_token(self, token, **kwargs):
        """Validate the token signature."""

        token = force_bytes(token)
        jws = JWS.from_compact(token)
        header = json.loads(jws.signature.protected)

        try:
            header.get("alg")
        except KeyError:
            msg = "No alg value found in header"
            raise SuspiciousOperation(msg)

        jwk_json = self.retrieve_matching_jwk(header)
        jwk = JWK.from_json(jwk_json)

        if not jws.verify(jwk):
            msg = "JWS token verification failed."
            raise SuspiciousOperation(msg)

        # The 'token' will always be a byte string since it's
        # the result of base64.urlsafe_b64decode().
        # The payload is always the result of base64.urlsafe_b64decode().
        # In Python 3 and 2, that's always a byte string.
        # In Python3.6, the json.loads() function can accept a byte string
        # as it will automagically decode it to a unicode string before
        # deserializing https://bugs.python.org/issue17909
        return json.loads(jws.payload.decode("utf-8"))

    def process_events(self, payload):
        """Save the events in the db, and enqueue jobs to act upon them"""

        fxa_uid = payload.get("sub")
        events = payload.get("events")

        try:
            user = get_user_model().objects.get(username=fxa_uid)
        except get_user_model().DoesNotExist:
            user = None
        print(user)

        if not user:
            return

        for long_id, event in events.items():
            short_id = long_id.replace(settings.FXA_SET_ID_PREFIX, "")
            if short_id == "password-change":
                event_type = AccountEvent.EventType.PASSWORD_CHANGED
            elif short_id == "profile-change":
                event_type = AccountEvent.EventType.PROFILE_CHANGED
            elif short_id == "subscription-state-change":
                event_type = AccountEvent.EventType.SUBSCRIPTION_CHANGED
            elif short_id == "delete-user":
                event_type = AccountEvent.EventType.PROFILE_DELETED
            else:
                event_type = None

            if not event_type:
                continue

            account_event = AccountEvent.objects.create(
                issued_at=payload["iat"],
                jwt_id=payload["jti"],
                fxa_uid=fxa_uid,
                status=AccountEvent.EventStatus.PENDING,
                payload=json.dumps(event),
                event_type=event_type,
            )

            if user:
                if event_type == AccountEvent.EventType.PROFILE_DELETED:
                    process_event_delete_user.delay(account_event.id)
                elif event_type == AccountEvent.EventType.SUBSCRIPTION_CHANGED:
                    process_event_subscription_state_change.delay(account_event.id)
                elif event_type == AccountEvent.EventType.PASSWORD_CHANGED:
                    process_event_password_change.delay(account_event.id)
                elif event_type == AccountEvent.EventType.PROFILE_CHANGED:
                    process_event_profile_change.delay(account_event.id)
                else:
                    pass

    def post(self, request, *args, **kwargs):
        authorization = request.META.get("HTTP_AUTHORIZATION")
        print(authorization)
        if not authorization:
            raise Http404

        auth = authorization.split()
        if auth[0].lower() != "bearer":
            raise Http404
        id_token = auth[1]

        payload = self.verify_token(id_token)

        if payload:
            issuer = payload["iss"]
            events = payload.get("events", "")
            fxa_uid = payload.get("sub", "")
            exp = payload.get("exp")

            # If the issuer is not Firefox Accounts raise a 404 error
            if settings.FXA_SET_ISSUER != issuer:
                raise Http404

            # If exp is in the token then it's an id_token that should not be here
            if any([not events, not fxa_uid, exp]):
                return HttpResponse(status=400)

            self.process_events(payload)

            return HttpResponse(status=202)
        raise Http404
