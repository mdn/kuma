from django.conf.urls import include, url
from django.views.generic import RedirectView

from kuma.attachments.feeds import AttachmentsFeed
from kuma.attachments.views import edit_attachment
from kuma.core.decorators import shared_cache_control

from . import feeds, views
from .constants import DOCUMENT_PATH_RE

# These patterns inherit (?P<document_path>[^\$]+).
document_patterns = [
    url(r'^$',
        views.document.document,
        name='wiki.document'),
    url(r'^\$api$',
        views.document.document_api,
        name='wiki.document_api'),
    url(r'^\$revision/(?P<revision_id>\d+)$',
        views.revision.revision,
        name='wiki.revision'),
    url(r'^\$history$',
        views.list.revisions,
        name='wiki.document_revisions'),
    url(r'^\$edit$',
        views.edit.edit,
        name='wiki.edit'),
    url(r'^\$files$',
        edit_attachment,
        name='attachments.edit_attachment'),
    url(r'^\$compare$',
        views.revision.compare,
        name='wiki.compare_revisions'),
    url(r'^\$children$',
        views.document.children,
        name='wiki.children'),
    url(r'^\$translate$',
        views.translate.translate,
        name='wiki.translate'),
    url(r'^\$locales$',
        views.translate.select_locale,
        name='wiki.select_locale'),
    url(r'^\$json$',
        views.document.as_json,
        name='wiki.json_slug'),
    url(r'^\$toc$',
        views.document.toc,
        name='wiki.toc'),
    url(r'^\$move$',
        views.document.move,
        name='wiki.move'),
    url(r'^\$quick-review$',
        views.revision.quick_review,
        name='wiki.quick_review'),
    url(r'^\$samples/(?P<sample_name>.+)/files/(?P<attachment_id>\d+)/(?P<filename>.+)$',
        views.code.raw_code_sample_file,
        name='wiki.raw_code_sample_file'),
    url(r'^\$samples/(?P<sample_name>.+)$',
        views.code.code_sample,
        name='wiki.code_sample'),
    url(r'^\$revert/(?P<revision_id>\d+)$',
        views.delete.revert_document,
        name='wiki.revert_document'),
    url(r'^\$repair_breadcrumbs$',
        views.document.repair_breadcrumbs,
        name='wiki.repair_breadcrumbs'),
    url(r'^\$delete$',
        views.delete.delete_document,
        name='wiki.delete_document'),

    # Un/Subscribe to document edit notifications.
    url(r'^\$subscribe$',
        views.document.subscribe,
        name='wiki.subscribe'),

    # Un/Subscribe to document tree edit notifications.
    url(r'^\$subscribe_to_tree$',
        views.document.subscribe_to_tree,
        name='wiki.subscribe_to_tree'),

]

non_document_patterns = [
    url(r'^ckeditor_config.js$',
        views.misc.ckeditor_config,
        name='wiki.ckeditor_config'),

    # internals
    url(r'^preview-wiki-content$',
        views.revision.preview,
        name='wiki.preview'),
    url(r'^get-documents$',
        views.misc.autosuggest_documents,
        name='wiki.autosuggest_documents'),

    # Special pages
    url(r'^tags$',
        views.list.tags,
        name='wiki.list_tags'),
    url(r'^tag/(?P<tag>.+)$',
        views.list.documents,
        name='wiki.tag'),
    url(r'^new$',
        views.create.create,
        name='wiki.create'),
    url(r'^all$',
        views.list.documents,
        name='wiki.all_documents'),
    url(r'^with-errors$',
        views.list.with_errors,
        name='wiki.errors'),
    url(r'^without-parent$',
        views.list.without_parent,
        name='wiki.without_parent'),
    url(r'^top-level$',
        views.list.top_level,
        name='wiki.top_level'),
    url(r'^needs-review/(?P<tag>[^/]+)$',
        views.list.needs_review,
        name='wiki.list_review_tag'),
    url(r'^needs-review/?',
        views.list.needs_review,
        name='wiki.list_review'),
    url(r'^localization-tag/(?P<tag>[^/]+)$',
        views.list.with_localization_tag,
        name='wiki.list_with_localization_tag'),
    url(r'^localization-tag/?',
        views.list.with_localization_tag,
        name='wiki.list_with_localization_tags'),

    # Legacy KumaScript macro list, when they were stored in Kuma database
    url(r'^templates$',
        shared_cache_control(s_maxage=60 * 60 * 24 * 30)(
            RedirectView.as_view(pattern_name='dashboards.macros',
                                 permanent=True)
        )),

    # Akismet Revision
    url(r'^submit_akismet_spam$',
        views.akismet_revision.submit_akismet_spam,
        name='wiki.submit_akismet_spam'),

    # Feeds
    url(r'^feeds/(?P<format>[^/]+)/all/?',
        shared_cache_control(feeds.DocumentsRecentFeed()),
        name="wiki.feeds.recent_documents"),
    url(r'^feeds/(?P<format>[^/]+)/l10n-updates/?',
        shared_cache_control(feeds.DocumentsUpdatedTranslationParentFeed()),
        name="wiki.feeds.l10n_updates"),
    url(r'^feeds/(?P<format>[^/]+)/tag/(?P<tag>[^/]+)',
        shared_cache_control(feeds.DocumentsRecentFeed()),
        name="wiki.feeds.recent_documents"),
    url(r'^feeds/(?P<format>[^/]+)/needs-review/(?P<tag>[^/]+)',
        shared_cache_control(feeds.DocumentsReviewFeed()),
        name="wiki.feeds.list_review_tag"),
    url(r'^feeds/(?P<format>[^/]+)/needs-review/?',
        shared_cache_control(feeds.DocumentsReviewFeed()),
        name="wiki.feeds.list_review"),
    url(r'^feeds/(?P<format>[^/]+)/revisions/?',
        shared_cache_control(feeds.RevisionsFeed()),
        name="wiki.feeds.recent_revisions"),
    url(r'^feeds/(?P<format>[^/]+)/files/?',
        shared_cache_control(AttachmentsFeed()),
        name="attachments.feeds.recent_files"),
]

lang_urlpatterns = non_document_patterns + [
    url(r'^(?P<document_path>%s)' % DOCUMENT_PATH_RE.pattern,
        include(document_patterns)),
]
