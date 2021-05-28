import importlib

from allauth.account import views as account_views
from allauth.socialaccount import providers
from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from kuma.core.decorators import redirect_in_maintenance_mode

from . import views


urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.package + ".urls")
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, "urlpatterns", None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns

lang_urlpatterns = [
    re_path(
        r"^users/signout/?$",
        redirect_in_maintenance_mode(csrf_exempt(account_views.logout)),
        name="account_logout",
    ),
    re_path(
        r"^users/account/signup/?$",
        redirect_in_maintenance_mode(views.signup),
        name="socialaccount_signup",
    ),
]
