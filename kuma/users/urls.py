import importlib

from django.conf.urls import include, url

from allauth.account import views as account_views
from allauth.socialaccount import providers, views as socialaccount_views

from . import views


account_patterns = [
    url(r'^signin/cancelled/?$',
        socialaccount_views.login_cancelled,
        name='socialaccount_login_cancelled'),
    url(r'^signin/error/?$',
        socialaccount_views.login_error,
        name='socialaccount_login_error'),
    url(r'^signup/?$',
        views.signup,
        name='socialaccount_signup'),
    url(r'^connections/?$',
        socialaccount_views.connections,
        name='socialaccount_connections'),
    url(r'^inactive/?$',
        account_views.account_inactive,
        name='account_inactive'),
    url(r'^email/?$',
        account_views.email,
        name='account_email'),
    url(r'^email/confirm/?$',
        account_views.email_verification_sent,
        name='account_email_verification_sent'),
    url(r'^email/confirm/(?P<key>\w+)/?$',
        account_views.confirm_email,
        name='account_confirm_email'),
    # Auth keys
    url(r'^keys', include('kuma.authkeys.urls')),
]


users_patterns = [
    url(r'^signup/?$',
        account_views.signup,
        name='account_signup'),
    url(r'^signin/?$',
        account_views.login,
        name='account_login'),
    url(r'^signout/?$',
        account_views.logout,
        name='account_logout'),
    url(r'^account/', include(account_patterns)),
    url(r'^ban/(?P<user_id>\d+)$',
        views.ban_user,
        name='users.ban_user'),
]


for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.package + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        users_patterns += prov_urlpatterns


urlpatterns = [
    url(r'^profiles/(?P<username>[^/]+)/?$',
        views.profile_view,
        name='users.profile'),
    url(r'^profiles/(?P<username>[^/]+)/edit$',
        views.profile_edit,
        name='users.profile_edit'),
    url(r'^profile/?$',
        views.my_profile,
        name='users.my_profile'),
    url(r'^profile/edit/?$',
        views.my_profile_edit,
        name='users.my_profile_edit'),
    url(r'^newsletter/?$',
        views.apps_newsletter,
        name='users.apps_newsletter'),
    url(r'^users/', include(users_patterns)),
]
