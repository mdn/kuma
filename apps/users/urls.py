from django.conf.urls.defaults import patterns, url, include

from users import views


# These will all start with /user/<user_id>/
detail_patterns = patterns('',
# TODO:
#    url('^$', views.profile, name='users.profile'),
#    url('^abuse', views.report_abuse, name='users.abuse'),
)

users_patterns = patterns('',
    url(r'^login$', views.login, name='users.login'),
    url(r'^logout$', views.logout, name='users.logout'),
    url(r'^register$', views.register, name='users.register'),
    url(r'^activate/(?P<activation_key>\w+)$', views.activate,
        name='users.activate'),
    url(r'^edit$', views.edit_profile, name='users.edit_profile'),

    # Password reset
    url(r'^pwreset$', views.password_reset, name='users.pw_reset'),
    url(r'^pwresetsent$', views.password_reset_sent,
        name='users.pw_reset_sent'),
    url(r'^pwreset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)$',
        views.password_reset_confirm, name="users.pw_reset_confirm"),
    url(r'^pwresetcomplete$', views.password_reset_complete,
        name="users.pw_reset_complete"),
)

urlpatterns = patterns('',
    # URLs for a single user.
    (r'^user/(?P<user_id>\d+)/', include(detail_patterns)),
    (r'^users/', include(users_patterns)),
)
