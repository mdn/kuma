from django.conf.urls.defaults import patterns, url, include

from sumo.views import redirect_to
from users import views


# These will all start with /user/<user_id>/
detail_patterns = patterns('',
    url(r'^$', views.profile, name='users.profile'),
# TODO:
#    url('^abuse', views.report_abuse, name='users.abuse'),
)

users_patterns = patterns('',
    url(r'^/browserid_verify$', views.browserid_verify,
        name='users.browserid_verify'),
    url(r'^/browserid_register$', views.browserid_register,
        name='users.browserid_register'),
    url(r'^/browserid_change_email$', views.browserid_change_email,
        name='users.browserid_change_email'),
    url(r'^/login$', views.login, name='users.login'),
    url(r'^/logout$', views.logout, name='users.logout'),
    url(r'^/register$', views.register, name='users.register'),
    url(r'^/activate/(?P<activation_key>\w+)$', views.activate,
        name='users.activate'),
    url(r'^/edit$', views.edit_profile, name='users.edit_profile'),
    url(r'^/avatar$', views.edit_avatar, name='users.edit_avatar'),
    url(r'^/avatar/delete$', views.delete_avatar, name='users.delete_avatar'),

    # Password reset
    url(r'^/pwreset$', views.password_reset, name='users.pw_reset'),
    url(r'^/pwresetsent$', views.password_reset_sent,
        name='users.pw_reset_sent'),
    url(r'^/pwreset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)$',
        views.password_reset_confirm, name="users.pw_reset_confirm"),
    url(r'^/pwresetcomplete$', views.password_reset_complete,
        name="users.pw_reset_complete"),

    # Change password
    url(r'^/pwchange$', views.password_change, name='users.pw_change'),
    url(r'^/pwchangecomplete$', views.password_change_complete,
        name='users.pw_change_complete'),

    url(r'^/resendconfirmation$', views.resend_confirmation,
        name='users.resend_confirmation'),
    url(r'^/sendemailreminder$', views.send_email_reminder,
        name='users.send_email_reminder'),

    # Change email
    url(r'^change_email$', redirect_to, {'url': 'users.change_email'},
        name='users.old_change_email'),
    url(r'^confirm_email/(?P<activation_key>\w+)$',
        redirect_to, {'url': 'users.confirm_email'},
        name='users.old_confirm_email'),
    url(r'^/change_email$', views.change_email, name='users.change_email'),
    url(r'^/confirm_email/(?P<activation_key>\w+)$',
        views.confirm_change_email, name='users.confirm_email'),
)

urlpatterns = patterns('',
    # URLs for a single user.
    # (r'^user/(?P<user_id>\d+)', include(detail_patterns)),
    (r'^users', include(users_patterns)),
)
