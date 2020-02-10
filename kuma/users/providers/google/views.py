from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (OAuth2CallbackView,
                                                          OAuth2LoginView)

from kuma.core.decorators import redirect_in_maintenance_mode
from kuma.core.ga_tracking import (
    ACTION_AUTH_STARTED,
    CATEGORY_SIGNUP_FLOW,
    track_event
)


class KumaOAuth2LoginView(OAuth2LoginView):

    def dispatch(self, request):
        track_event(CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, 'google')
        return super().dispatch(request)


oauth2_login = redirect_in_maintenance_mode(
    KumaOAuth2LoginView.adapter_view(GoogleOAuth2Adapter)
)
oauth2_callback = redirect_in_maintenance_mode(
    OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
)
