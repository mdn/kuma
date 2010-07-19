from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('flagit.views',
    url(r'^$', 'queue', name='flagit.queue'),
    url(r'^/flag$', 'flag', name='flagit.flag'),
    url(r'^/update/(?P<flagged_object_id>\d+)$', 'update',
        name='flagit.update'),
)
