import importlib

from allauth.account import views as account_views
from allauth.socialaccount import providers, views as socialaccount_views
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt

from kuma.authkeys.views import list as list_keys
from kuma.core.decorators import redirect_in_maintenance_mode

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
    url(r'^signup-landing/?$',
        views.signin_landing,
        name='socialaccount_signin'),
    url(r'^inactive/?$',
        account_views.account_inactive,
        name='account_inactive'),
    url(r'^email/?$',
        account_views.email,
        name='account_email'),
    url(r'^email/confirm/?$',
        account_views.email_verification_sent,
        name='account_email_verification_sent'),
    url(r'^email/confirm/(?P<key>[-:\w]+)/?$',
        redirect_in_maintenance_mode(account_views.confirm_email),
        name='account_confirm_email'),
    # Auth keys
    url(r'^keys$', list_keys, name='authkeys.list'),
    url(r'^keys/', include('kuma.authkeys.urls')),
]


users_patterns = [
    url(r'^signup/?$',
        redirect_in_maintenance_mode(account_views.signup),
        name='account_signup'),
    url(r'^signin/?$',
        redirect_in_maintenance_mode(account_views.login),
        name='account_login'),
    url(r'^signout/?$',
        redirect_in_maintenance_mode(csrf_exempt(account_views.logout)),
        name='account_logout'),
    url(r'^account/', include(account_patterns)),
    url(r'^ban/(?P<username>[^/]+)$',
        views.ban_user,
        name='users.ban_user'),
    url(r'^ban_user_and_cleanup/(?P<username>[^/]+)$',
        views.ban_user_and_cleanup,
        name='users.ban_user_and_cleanup'),
    url(r'^ban_user_and_cleanup_summary/(?P<username>[^/]+)$',
        views.ban_user_and_cleanup_summary,
        name='users.ban_user_and_cleanup_summary'),
    url(r'^account/recover/send',
        views.send_recovery_email,
        name='users.send_recovery_email'),
    url(r'^account/recover/sent',
        views.recovery_email_sent,
        name='users.recovery_email_sent'),
    url(r'^account/recover/done',
        views.recover_done,
        name='users.recover_done'),
    url(r'^account/recover/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        views.recover,
        name='users.recover'),
]


urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.package + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns

lang_urlpatterns = [
    url(r'^profiles/(?P<username>[^/]+)/?$',
        views.user_detail,
        name='users.user_detail'),
    url(r'^profiles/(?P<username>[^/]+)/edit$',
        views.user_edit,
        name='users.user_edit'),
    url(r'^profiles/(?P<username>[^/]+)/delete$',
        views.user_delete,
        name='users.user_delete'),
    url(r'^profile/stripe_subscription$',
        views.create_stripe_subscription,
        name='users.create_stripe_subscription'),
    url(r'^profile/?$',
        views.my_detail_page,
        name='users.my_detail_page'),
    url(r'^profile/edit/?$',
        views.my_edit_page,
        name='users.my_edit_page'),
    url(r'^users/', include(users_patterns)),
]
