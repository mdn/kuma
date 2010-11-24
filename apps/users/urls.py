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

    # Password reset
    url(r'^pwreset$', views.password_reset, name='users.pw_reset'),
    url(r'^pwresetsent$', views.password_reset_sent,
        name='users.pw_reset_sent'),
    url(r'^pwreset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)$',
        views.password_reset_confirm, name="users.pw_reset_confirm"),
    url(r'^pwresetcomplete$', views.password_reset_complete,
        name="users.pw_reset_complete"),

# TODO:
#    url('^confirm/resend$', views.confirm_resend, name='users.confirm.resend'),
#    url('^confirm/(?P<token>[-\w]+)$', views.confirm, name='users.confirm'),
#    url(r'^emailchange/(?P<token>[-\w]+={0,3})/(?P<hash>[\w]+)$',
#                        views.emailchange, name="users.emailchange"),
)

urlpatterns = patterns('',
    # URLs for a single user.
    (r'^user/(?P<user_id>\d+)/', include(detail_patterns)),
    (r'^users/', include(users_patterns)),
)
