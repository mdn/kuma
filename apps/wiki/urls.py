from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('wiki.views',

    # Un/Subscribe to locale 'ready for review' notifications.
    url(r'^/watch-ready-for-review$', 'watch_locale',
        name='wiki.locale_watch'),
    url(r'^/unwatch-ready-for-review$', 'unwatch_locale',
        name='wiki.locale_unwatch'),

    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/preview-wiki-content$', 'preview_revision', name='wiki.preview'),
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    url(r'^/(?P<document_slug>[^\/]+)$', 'document',
        name='wiki.document'),
    url(r'^/(?P<document_slug>[^\/]+)/revision/(?P<revision_id>\d+)$',
        'revision', name='wiki.revision'),
    url(r'^/(?P<document_slug>[^\/]+)/history$',
        'document_revisions', name='wiki.document_revisions'),
    url(r'^/(?P<document_slug>[^\/]+)/edit$', 'new_revision',
        name='wiki.new_revision'),
    url(r'^/(?P<document_slug>[^\/]+)/edit/(?P<revision_id>\d+)$',
        'new_revision', name='wiki.new_revision_based_on'),
    url(r'^/(?P<document_slug>[^\/]+)/review/(?P<revision_id>\d+)$',
        'review_revision', name='wiki.review_revision'),
    url(r'^/(?P<document_slug>[^\/]+)/compare$',
        'compare_revisions', name='wiki.compare_revisions'),
    url(r'^/(?P<document_slug>[^\/]+)/translate$',
        'translate', name='wiki.translate'),

    # Un/Subscribe to document edit notifications.
    url(r'^/(?P<document_slug>[^\/]+)/watch$', 'watch_document',
        name='wiki.document_watch'),
    url(r'^/(?P<document_slug>[^\/]+)/unwatch$', 'unwatch_document',
        name='wiki.document_unwatch'),
)
