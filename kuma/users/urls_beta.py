import importlib

from allauth.account import views as account_views
from allauth.socialaccount import providers
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt

from kuma.core.decorators import redirect_in_maintenance_mode


urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.package + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns

users_patterns = [
    url(r'^signup/?$',
        redirect_in_maintenance_mode(account_views.signup),
        name='account_signup'),
    url(r'^signin/?$',
        redirect_in_maintenance_mode(account_views.login),
        name='account_login'),
    url(r'^signout/?$',
        redirect_in_maintenance_mode(csrf_exempt(account_views.logout)),
        name='account_logout')
]

lang_urlpatterns = [
    url(r'^users/', include(users_patterns)),
]
