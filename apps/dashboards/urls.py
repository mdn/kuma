from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

urlpatterns = patterns('dashboards.views',
    url(r'^$', redirect_to, {'url': 'home'}),
    url(r'^home/$', 'home', name='home'),
    # TODO: mobile home page
    # TODO: live chat page
    # TODO: contributor dashboard
    # TODO: l10n dashboard (may be part of wiki app instead)
)
