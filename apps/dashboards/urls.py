from django.conf.urls import patterns, url
from django.views.generic.simple import redirect_to


urlpatterns = patterns('dashboards.views',
    url(r'^dashboards/revisions$', 'revisions', name='dashboards.revisions'),
    url(r'^dashboards/user_lookup$', 'user_lookup',
        name='dashboards.user_lookup'),
    url(r'^dashboards/topic_lookup$', 'topic_lookup',
        name='dashboards.topic_lookup'),

    url(r'^dashboards/localization$', redirect_to,
        {'url': '/docs/MDN/Doc_status/Overview'}),
)
