from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to


urlpatterns = patterns('dashboards.views',
    url(r'^$', redirect_to, {'url': 'home'}),
    url(r'^home/$', 'home', name='home'),
    url(r'^mobile/$', 'mobile', name='home.mobile'),
    url(r'^contributors$', 'contributors', name='dashboards.contributors'),
    # TODO: more contributor dashboard
    url(r'^localization$', 'localization', name='dashboards.localization'),
    url(r'^localization/(?P<readout>[^/]+)', 'localization_detail',
        name='dashboards.localization_detail'),
)
