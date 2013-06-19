from django.conf.urls import patterns, url


urlpatterns = patterns('dashboards.views',
    url(r'^dashboards/revisions$', 'revisions', name='dashboards.revisions'),
    url(r'^dashboards/user_lookup$', 'user_lookup',
        name='dashboards.user_lookup'),
    url(r'^dashboards/topic_lookup$', 'topic_lookup',
        name='dashboards.topic_lookup'),

    url(r'^dashboards/localization$', 'localization', name='dashboards.localization'),
    url(r'^dashboards/fetch_localization_data$', 'fetch_localization_data',
        name='dashboards.fetch_localization_data'),
)
