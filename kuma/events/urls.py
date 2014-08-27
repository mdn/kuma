from django.conf.urls import patterns, url

urlpatterns = patterns('kuma.events.views',
    url(r'^$', 'events', name='events'),
)
