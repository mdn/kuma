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

urlpatterns = patterns('',
    url(r'^profiles/(?P<username>[^/]+)/?$', views.profile_view,
        name="users.profile"),
    url(r'^profiles/(?P<username>[^/]+)/roles$', user_roles,
        name="users.roles"),
    url(r'^profiles/(?P<username>[^/]+)/edit$', views.profile_edit,
        name="users.profile_edit"),
    url(r'^profile/?$', views.my_profile,
        name="users.my_profile"),
    url(r'^profile/edit/?$', views.my_profile_edit,
        name="users.my_profile_edit"),
    url(r'^newsletter/?$', 'kuma.users.views.apps_newsletter',
        name='users.apps_newsletter'),
    url(r'^users/', include(users_patterns)),
)
