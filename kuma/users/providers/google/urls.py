from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import KumaGoogleProvider

urlpatterns = default_urlpatterns(KumaGoogleProvider)
