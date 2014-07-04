from django.conf.urls import include, patterns, url

from allauth.account.views import login, logout
from teamwork.views import user_roles
from . import views

users_patterns = patterns('',
    url(r'^social/signup/$', views.signup, name='socialaccount_signup'),
    url(r'^', include('allauth.urls')),
    url(r"^signin/$", login, name="account_login"),
    url(r"^signout/$", logout, name="account_logout"),
    url(r'^ban/(?P<user_id>\d+)$', views.ban_user, name='users.ban_user'),
)

profiles_patterns = patterns('',
    url(r'^edit/?$', views.my_profile_edit, name="users.my_profile_edit"),
    url(r'^(?P<username>[^/]+)/?$', views.profile_view, name="users.profile"),
    url(r'^(?P<username>[^/]+)/roles$', user_roles, name="users.roles"),
    url(r'^(?P<username>[^/]+)/edit$', views.profile_edit, name="users.profile_edit"),
    url(r'^$', views.my_profile, name="users.my_profile"),
)

urlpatterns = patterns('',
    # BrowserID Realm
    url(r'^\.well-known/browserid-realm', 'kuma.users.views.browserid_realm', name='users.browserid-realm'),
    url(r'^newsletter/?$', 'kuma.users.views.apps_newsletter', name='apps_newsletter'),
    url(r'^profiles/', include(profiles_patterns)),
    url(r'^users/', include(users_patterns)),
)
