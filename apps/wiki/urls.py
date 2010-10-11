from django.conf.urls.defaults import patterns, url, include


# These URLs inherit (?P<document_slug>[^\/]).
document_patterns = patterns('wiki.views',
    url(r'^$', 'document', name='wiki.document'),
    url(r'^/revision/(?P<revision_id>\d+)$', 'revision',
        name='wiki.revision'),
    url(r'^/history$', 'document_revisions', name='wiki.document_revisions'),
    url(r'^/edit$', 'edit_document', name='wiki.edit_document'),
    url(r'^/edit/(?P<revision_id>\d+)$', 'edit_document',
        name='wiki.new_revision_based_on'),
    url(r'^/review/(?P<revision_id>\d+)$', 'review_revision',
        name='wiki.review_revision'),
    url(r'^/compare$', 'compare_revisions', name='wiki.compare_revisions'),
    url(r'^/translate$', 'translate', name='wiki.translate'),

    # Un/Subscribe to document edit notifications.
    url(r'^/watch$', 'watch_document', name='wiki.document_watch'),
    url(r'^/unwatch$', 'unwatch_document', name='wiki.document_unwatch'),
)

urlpatterns = patterns('wiki.views',

    # TODO: update view to the kb landing/home page when we have it
    url(r'^$', 'list_documents', name='wiki.home'),

    # Un/Subscribe to locale 'ready for review' notifications.
    url(r'^/watch-ready-for-review$', 'watch_locale',
        name='wiki.locale_watch'),
    url(r'^/unwatch-ready-for-review$', 'unwatch_locale',
        name='wiki.locale_unwatch'),
    url(r'^/json$', 'json_view', name='wiki.json'),

    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/preview-wiki-content$', 'preview_revision', name='wiki.preview'),
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    (r'^/(?P<document_slug>[^\/]+)', include(document_patterns)),
)
