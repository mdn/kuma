from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('wiki.views',
    url(r'^/(?P<document_slug>[\+\w]+)$', 'document', name='wiki.document'),
)
