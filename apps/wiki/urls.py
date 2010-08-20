from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('wiki.views',
    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    url(r'^/(?P<document_slug>[\+\w]+)$', 'document', name='wiki.document'),
    url(r'^/(?P<document_id>\d+)/history$', 'document_revisions',
        name='wiki.document_revisions'),
    url(r'^/(?P<document_id>\d+)/edit', 'new_revision', name='wiki.new_revision'),
)
