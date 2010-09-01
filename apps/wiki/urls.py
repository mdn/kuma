from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('wiki.views',
    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    url(r'^/(?P<document_slug>[^\/]+)$', 'document',
        name='wiki.document'),
    url(r'^/(?P<document_slug>[^\/]+)/history$',
        'document_revisions', name='wiki.document_revisions'),
    url(r'^/(?P<document_slug>[^\/]+)/edit$', 'new_revision',
        name='wiki.new_revision'),
    url(r'^/(?P<document_slug>[^\/]+)/edit/(?P<revision_id>\d+)$',
        'new_revision', name='wiki.new_revision_based_on'),
    url(r'^/(?P<document_slug>[^\/]+)/review/(?P<revision_id>\d+)$',
        'review_revision', name='wiki.review_revision'),
)
