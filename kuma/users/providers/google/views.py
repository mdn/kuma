from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (OAuth2CallbackView,
                                                          OAuth2LoginView)

from kuma.core.decorators import redirect_in_maintenance_mode


oauth2_login = redirect_in_maintenance_mode(
    OAuth2LoginView.adapter_view(GoogleOAuth2Adapter)
)
oauth2_callback = redirect_in_maintenance_mode(
    OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
)
