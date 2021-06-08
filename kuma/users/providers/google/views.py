from urllib.parse import urlparse

from allauth.account.utils import get_next_redirect_url
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)

from kuma.core.decorators import redirect_in_maintenance_mode
from kuma.core.ga_tracking import ACTION_AUTH_STARTED, CATEGORY_SIGNUP_FLOW, track_event


class KumaOAuth2LoginView(OAuth2LoginView):
    def dispatch(self, request):
        # TODO: Figure out a way to NOT trigger the "ACTION_AUTH_STARTED" when
        # simply following the link. We've seen far too many submissions when
        # curl or some browser extensions follow the link but not actually being
        # users who proceed "earnestly".
        # For now, to make a simple distinction between uses of `curl` and normal
        # browser clicks we check that a HTTP_REFERER is actually set and comes
        # from the same host as the request.
        # Note! This is the same in kuma.users.providers.github.KumaOAuth2LoginView
        # See https://github.com/mdn/kuma/issues/6759
        http_referer = request.META.get("HTTP_REFERER")
        if http_referer:
            if urlparse(http_referer).netloc == request.get_host():
                track_event(CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, "google")

        next_url = get_next_redirect_url(request)
        if next_url:
            request.session["sociallogin_next_url"] = next_url

        return super().dispatch(request)


oauth2_login = redirect_in_maintenance_mode(
    KumaOAuth2LoginView.adapter_view(GoogleOAuth2Adapter)
)
oauth2_callback = redirect_in_maintenance_mode(
    OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
)
