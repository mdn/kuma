from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView

from sumo.views import redirect_to
from wiki.feeds import (DocumentsRecentFeed, DocumentsReviewFeed, RevisionsFeed,
                        AttachmentsFeed,
                        DocumentsUpdatedTranslationParentFeed,)


# These patterns inherit (?P<document_path>[^\$]+).
document_patterns = patterns('wiki.views',
    url(r'^$', 'document', name='wiki.document'),
    url(r'^\$revision/(?P<revision_id>\d+)$', 'revision',
        name='wiki.revision'),
    url(r'^\$history$', 'document_revisions', name='wiki.document_revisions'),
    url(r'^\$edit$', 'edit_document', name='wiki.edit_document'),
    url(r'^\$edit/(?P<revision_id>\d+)$', 'edit_document',
        name='wiki.new_revision_based_on'),
    url(r'^\$review/(?P<revision_id>\d+)$', 'review_revision',
        name='wiki.review_revision'),
    url(r'^\$compare$', 'compare_revisions', name='wiki.compare_revisions'),
    url(r'^\$children$', 'get_children', name='wiki.get_children'),
    url(r'^\$translate$', 'translate', name='wiki.translate'),
    url(r'^\$locales$', 'select_locale', name='wiki.select_locale'),
    url(r'^\$json$', 'json_view', name='wiki.json_slug'),
    url(r'^\$styles$', 'styles_view', name='wiki.styles'),
    url(r'^\$toc$', 'toc_view', name='wiki.toc'),
    url(r'^\$move$', 'move', name='wiki.move'),
    url(r'^\$quick-review$', 'quick_review', name='wiki.quick_review'),
    url(r'^\$samples/(?P<sample_id>.+)$', 'code_sample', name='wiki.code_sample'),
    url(r'^\$revert/(?P<revision_id>\d+)$', 'revert_document',
        name='wiki.revert_document'),
    url(r'^\$repair_breadcrumbs$',
        'repair_breadcrumbs',
        name='wiki.repair_breadcrumbs'),
    url(r'^\$delete$',
        'delete_document',
        name='wiki.delete_document'),
    url(r'^\$restore$',
        'restore_document',
        name='wiki.restore_document'),
    url(r'^\$purge$',
        'purge_document',
        name='wiki.purge_document'),

    # Un/Subscribe to document edit notifications.
    url(r'^\$watch$', 'watch_document', name='wiki.document_watch'),
    url(r'^\$unwatch$', 'unwatch_document', name='wiki.document_unwatch'),

    # Vote helpful/not helpful
    url(r'^\$vote', 'helpful_vote', name="wiki.document_vote"),
)

urlpatterns = patterns('docs.views',
    url(r'^/?$', 'docs', name='docs'),
)

urlpatterns += patterns('wiki.views',
    # Un/Subscribe to locale 'ready for review' notifications.
    url(r'^/ckeditor_config.js$', 'ckeditor_config',
        name='wiki.ckeditor_config'),
    url(r'^/watch-ready-for-review$', 'watch_locale',
        name='wiki.locale_watch'),
    url(r'^/unwatch-ready-for-review$', 'unwatch_locale',
        name='wiki.locale_unwatch'),

    # Un/Subscribe to 'approved' notifications.
    url(r'^/watch-approved$', 'watch_approved',
        name='wiki.approved_watch'),
    url(r'^/unwatch-approved$', 'unwatch_approved',
        name='wiki.approved_unwatch'),

    url(r'^.json$', 'json_view', name='wiki.json'),

    url(r'^/templates$', 'list_templates', name='wiki.list_templates'),
    url(r'^/files$', 'list_files', name='wiki.list_files'),
    url(r'^/tags$', 'list_tags', name='wiki.list_tags'),
    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/preview-wiki-content$', 'preview_revision', name='wiki.preview'),

    url(r'^/move-requested$',
        TemplateView.as_view(template_name='wiki/move_requested.html'),
        name='wiki.move_requested'),
    
    url(r'^/get-documents$', 'autosuggest_documents', name='wiki.autosuggest_documents'),
    url(r'^/external-signup$', 'external_signup', name='wiki.external_signup'),
    
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    url(r'^/needs-review/(?P<tag>[^/]+)$', 'list_documents_for_review',
        name='wiki.list_review_tag'),
    url(r'^/needs-review/?', 'list_documents_for_review',
        name='wiki.list_review'),

    url(r'^/feeds/(?P<format>[^/]+)/all/?',
        DocumentsRecentFeed(), name="wiki.feeds.recent_documents"),
    url(r'^/feeds/(?P<format>[^/]+)/l10n-updates/?',
        DocumentsUpdatedTranslationParentFeed(), name="wiki.feeds.l10n_updates"),
    url(r'^/feeds/(?P<format>[^/]+)/tag/(?P<tag>[^/]+)',
        DocumentsRecentFeed(), name="wiki.feeds.recent_documents"),
    url(r'^/feeds/(?P<format>[^/]+)/category/(?P<category>[^/]+)',
        DocumentsRecentFeed(), name="wiki.feeds.recent_documents_category"),
    url(r'^/feeds/(?P<format>[^/]+)/needs-review/(?P<tag>[^/]+)',
        DocumentsReviewFeed(), name="wiki.feeds.list_review_tag"),
    url(r'^/feeds/(?P<format>[^/]+)/needs-review/?',
        DocumentsReviewFeed(), name="wiki.feeds.list_review"),
    url(r'^/feeds/(?P<format>[^/]+)/revisions/?',
        RevisionsFeed(), name="wiki.feeds.recent_revisions"),
    url(r'^/feeds/(?P<format>[^/]+)/files/?',
        AttachmentsFeed(), name="wiki.feeds.recent_files"),

    url(r'^/tag/(?P<tag>.+)$', 'list_documents', name='wiki.tag'),

    url(r'^/load/$', 'load_documents', name='wiki.load_documents'),

    (r'^/(?P<document_path>[^\$]+)', include(document_patterns)),
)
