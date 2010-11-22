from django.conf.urls.defaults import patterns, url, include

from users import views


# These will all start with /user/<user_id>/
detail_patterns = patterns('',
# TODO:
#    url('^$', views.profile, name='users.profile'),
#    url('^abuse', views.report_abuse, name='users.abuse'),
)

users_patterns = patterns('',
    url('^login', views.login, name='users.login'),
    url('^logout', views.logout, name='users.logout'),
# TODO:
#    url('^register$', views.register, name='users.register'),
#    url(r'^pwreset/?$', auth_views.password_reset,
#                        {'template_name': 'users/pwreset_request.html',
#                         'email_template_name': 'users/email/pwreset.ltxt',
#                         'password_reset_form': forms.PasswordResetForm,
#                        }, name="users.pwreset"),
#    url(r'^pwresetsent$', auth_views.password_reset_done,
#                        {'template_name': 'users/pwreset_sent.html'},
#                        name="users.pwreset_sent"),
#    url(r'^pwreset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)$',
#                        auth_views.password_reset_confirm,
#                        {'template_name': 'users/pwreset_confirm.html',
#                         'set_password_form': forms.SetPasswordForm,
#                        }, name="users.pwreset_confirm"),
#    url(r'^pwresetcomplete$', auth_views.password_reset_complete,
#                        {'template_name': 'users/pwreset_complete.html'},
#                        name="users.pwreset_complete"),
#    url('^confirm/resend$', views.confirm_resend, name='users.confirm.resend'),
#    url('^confirm/(?P<token>[-\w]+)$', views.confirm, name='users.confirm'),
#    url(r'^emailchange/(?P<token>[-\w]+={0,3})/(?P<hash>[\w]+)$',
#                        views.emailchange, name="users.emailchange"),
)

urlpatterns = patterns('',
    # URLs for a single user.
    ('^user/(?P<user_id>\d+)/', include(detail_patterns)),
    ('^users/', include(users_patterns)),
)
