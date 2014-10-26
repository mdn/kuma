from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView


urlpatterns = patterns('kuma.dashboards.views',
    url(r'^dashboards/revisions$', 'revisions',
        name='dashboards.revisions'),
    url(r'^dashboards/user_lookup$', 'user_lookup',
        name='dashboards.user_lookup'),
    url(r'^dashboards/topic_lookup$', 'topic_lookup',
        name='dashboards.topic_lookup'),
    url(r'^dashboards/localization$',
        RedirectView.as_view(url='/docs/MDN/Doc_status/Overview')),
)
