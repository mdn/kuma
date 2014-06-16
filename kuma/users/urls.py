from django.conf.urls import include, patterns, url

from teamwork.views import user_roles
from . import views

users_patterns = patterns('',
    url(r'^browserid_verify$', views.browserid_verify,
        name='users.browserid_verify'),
    url(r'^browserid_register$', views.browserid_register,
        name='users.browserid_register'),
    url(r'^browserid_change_email$', views.browserid_change_email,
        name='users.browserid_change_email'),
    url(r'^login$', views.login, name='users.login'),
    url(r'^logout$', views.logout, name='users.logout'),
    url(r'^change_email$', views.change_email, name='users.change_email'),
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
    url(r'^users/', include(users_patterns)),
)
