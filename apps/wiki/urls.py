from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('wiki.views',
    url(r'^/(?P<document_id>\d+)$', 'document', name='wiki.document'),
)
