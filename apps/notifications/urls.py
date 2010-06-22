from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('notifications.views',
    url(r'^/remove/(?P<key>\w+)$', 'remove', name='notifications.remove'),
    url(r'^/removed$', 'removed', name='notifications.removed'),
)
