import importlib

from allauth.account import views as account_views
from allauth.socialaccount import providers, views as socialaccount_views
from django.urls import include, re_path
from django.views.decorators.csrf import csrf_exempt

from kuma.core.decorators import redirect_in_maintenance_mode

from . import views


account_patterns = [
    re_path(
        r"^signin/cancelled/?$",
        socialaccount_views.login_cancelled,
        name="socialaccount_login_cancelled",
    ),
    re_path(
        r"^signin/error/?$",
        socialaccount_views.login_error,
        name="socialaccount_login_error",
    ),
    re_path(r"^signup/?$", views.signup, name="socialaccount_signup"),
    re_path(r"^signup-landing/?$", views.signin_landing, name="socialaccount_signin"),
    re_path(r"^inactive/?$", account_views.account_inactive, name="account_inactive"),
    re_path(r"^email/?$", account_views.email, name="account_email"),
    re_path(
        r"^email/confirm/?$",
        account_views.email_verification_sent,
        name="account_email_verification_sent",
    ),
    re_path(
        r"^email/confirm/(?P<key>[-:\w]+)/?$",
        redirect_in_maintenance_mode(account_views.confirm_email),
        name="account_confirm_email",
    ),
]


users_patterns = [
    re_path(
        r"^signup/?$",
        redirect_in_maintenance_mode(account_views.signup),
        name="account_signup",
    ),
    re_path(
        r"^signin/?$",
        redirect_in_maintenance_mode(account_views.login),
        name="account_login",
    ),
    re_path(
        r"^signout/?$",
        redirect_in_maintenance_mode(csrf_exempt(account_views.logout)),
        name="account_logout",
    ),
    re_path(r"^account/", include(account_patterns)),
    re_path(r"^ban/(?P<username>[^/]+)$", views.ban_user, name="users.ban_user"),
    re_path(
        r"^ban_user_and_cleanup/(?P<username>[^/]+)$",
        views.ban_user_and_cleanup,
        name="users.ban_user_and_cleanup",
    ),
    re_path(
        r"^ban_user_and_cleanup_summary/(?P<username>[^/]+)$",
        views.ban_user_and_cleanup_summary,
        name="users.ban_user_and_cleanup_summary",
    ),
    re_path(
        r"^account/recover/send",
        views.send_recovery_email,
        name="users.send_recovery_email",
    ),
    re_path(
        r"^account/recover/sent",
        views.recovery_email_sent,
        name="users.recovery_email_sent",
    ),
    re_path(r"^account/recover/done", views.recover_done, name="users.recover_done"),
    re_path(
        r"^account/recover/(?P<uidb64>[0-9A-Za-z_\-]+)/"
        r"(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$",
        views.recover,
        name="users.recover",
    ),
]


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
        r"^profiles/(?P<username>[^/]+)/?$", views.user_detail, name="users.user_detail"
    ),
    re_path(
        r"^profiles/(?P<username>[^/]+)/edit$", views.user_edit, name="users.user_edit"
    ),
    re_path(
        r"^profiles/(?P<username>[^/]+)/delete$",
        views.user_delete,
        name="users.user_delete",
    ),
    re_path(
        r"^profile/stripe_subscription$",
        views.create_stripe_subscription,
        name="users.create_stripe_subscription",
    ),
    re_path(r"^profile/?$", views.my_detail_page, name="users.my_detail_page"),
    re_path(r"^profile/edit/?$", views.my_edit_page, name="users.my_edit_page"),
    re_path(r"^users/", include(users_patterns)),
]
