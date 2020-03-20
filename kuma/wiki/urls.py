from django.urls import include, re_path
from django.views.generic import RedirectView

from kuma.attachments.feeds import AttachmentsFeed
from kuma.attachments.views import edit_attachment
from kuma.core.decorators import ensure_wiki_domain, shared_cache_control


from . import feeds, views
from .constants import DOCUMENT_PATH_RE

# These patterns inherit (?P<document_path>[^\$]+).
document_patterns = [
    re_path(r"^$", views.document.document, name="wiki.document"),
    re_path(r"^\$api$", views.document.document_api, name="wiki.document_api"),
    re_path(r"^\$revision$", views.revision.revision_api, name="wiki.revision_api"),
    re_path(
        r"^\$revision/(?P<revision_id>\d+)$",
        views.revision.revision,
        name="wiki.revision",
    ),
    re_path(r"^\$history$", views.list.revisions, name="wiki.document_revisions"),
    re_path(r"^\$edit$", views.edit.edit, name="wiki.edit"),
    re_path(r"^\$files$", edit_attachment, name="attachments.edit_attachment"),
    re_path(r"^\$compare$", views.revision.compare, name="wiki.compare_revisions"),
    re_path(r"^\$children$", views.document.children, name="wiki.children"),
    re_path(r"^\$translate$", views.translate.translate, name="wiki.translate"),
    re_path(r"^\$locales$", views.translate.select_locale, name="wiki.select_locale"),
    re_path(r"^\$json$", views.document.as_json, name="wiki.json_slug"),
    re_path(r"^\$toc$", views.document.toc, name="wiki.toc"),
    re_path(r"^\$move$", views.document.move, name="wiki.move"),
    re_path(r"^\$quick-review$", views.revision.quick_review, name="wiki.quick_review"),
    re_path(
        r"^\$samples/(?P<sample_name>.+)/files/(?P<attachment_id>\d+)/(?P<filename>.+)$",
        views.code.raw_code_sample_file,
        name="wiki.raw_code_sample_file",
    ),
    re_path(
        r"^\$samples/(?P<sample_name>.+)$",
        views.code.code_sample,
        name="wiki.code_sample",
    ),
    re_path(
        r"^\$revert/(?P<revision_id>\d+)$",
        views.delete.revert_document,
        name="wiki.revert_document",
    ),
    re_path(
        r"^\$repair_breadcrumbs$",
        views.document.repair_breadcrumbs,
        name="wiki.repair_breadcrumbs",
    ),
    re_path(r"^\$delete$", views.delete.delete_document, name="wiki.delete_document"),
    re_path(
        r"^\$restore$", views.delete.restore_document, name="wiki.restore_document"
    ),
    re_path(r"^\$purge$", views.delete.purge_document, name="wiki.purge_document"),
    # Un/Subscribe to document edit notifications.
    re_path(r"^\$subscribe$", views.document.subscribe, name="wiki.subscribe"),
    # Un/Subscribe to document tree edit notifications.
    re_path(
        r"^\$subscribe_to_tree$",
        views.document.subscribe_to_tree,
        name="wiki.subscribe_to_tree",
    ),
]

non_document_patterns = [
    re_path(
        r"^ckeditor_config.js$", views.misc.ckeditor_config, name="wiki.ckeditor_config"
    ),
    # internals
    re_path(r"^preview-wiki-content$", views.revision.preview, name="wiki.preview"),
    re_path(
        r"^get-documents$",
        views.misc.autosuggest_documents,
        name="wiki.autosuggest_documents",
    ),
    # Special pages
    re_path(r"^tags$", views.list.tags, name="wiki.list_tags"),
    re_path(r"^tag/(?P<tag>.+)$", views.list.documents, name="wiki.tag"),
    re_path(r"^new$", views.create.create, name="wiki.create"),
    re_path(r"^all$", views.list.documents, name="wiki.all_documents"),
    re_path(r"^with-errors$", views.list.with_errors, name="wiki.errors"),
    re_path(r"^without-parent$", views.list.without_parent, name="wiki.without_parent"),
    re_path(r"^top-level$", views.list.top_level, name="wiki.top_level"),
    re_path(
        r"^needs-review/(?P<tag>[^/]+)$",
        views.list.needs_review,
        name="wiki.list_review_tag",
    ),
    re_path(r"^needs-review/?", views.list.needs_review, name="wiki.list_review"),
    re_path(
        r"^localization-tag/(?P<tag>[^/]+)$",
        views.list.with_localization_tag,
        name="wiki.list_with_localization_tag",
    ),
    re_path(
        r"^localization-tag/?",
        views.list.with_localization_tag,
        name="wiki.list_with_localization_tags",
    ),
    # Legacy KumaScript macro list, when they were stored in Kuma database
    re_path(
        r"^templates$",
        ensure_wiki_domain(
            shared_cache_control(s_maxage=60 * 60 * 24 * 30)(
                RedirectView.as_view(pattern_name="dashboards.macros", permanent=True)
            )
        ),
    ),
    # Akismet Revision
    re_path(
        r"^submit_akismet_spam$",
        views.akismet_revision.submit_akismet_spam,
        name="wiki.submit_akismet_spam",
    ),
    # Feeds
    re_path(
        r"^feeds/(?P<format>[^/]+)/all/?",
        shared_cache_control(feeds.DocumentsRecentFeed()),
        name="wiki.feeds.recent_documents",
    ),
    re_path(
        r"^feeds/(?P<format>[^/]+)/l10n-updates/?",
        shared_cache_control(feeds.DocumentsUpdatedTranslationParentFeed()),
        name="wiki.feeds.l10n_updates",
    ),
    re_path(
        r"^feeds/(?P<format>[^/]+)/tag/(?P<tag>[^/]+)",
        shared_cache_control(feeds.DocumentsRecentFeed()),
        name="wiki.feeds.recent_documents",
    ),
    re_path(
        r"^feeds/(?P<format>[^/]+)/needs-review/(?P<tag>[^/]+)",
        shared_cache_control(feeds.DocumentsReviewFeed()),
        name="wiki.feeds.list_review_tag",
    ),
    re_path(
        r"^feeds/(?P<format>[^/]+)/needs-review/?",
        shared_cache_control(feeds.DocumentsReviewFeed()),
        name="wiki.feeds.list_review",
    ),
    re_path(
        r"^feeds/(?P<format>[^/]+)/revisions/?",
        shared_cache_control(feeds.RevisionsFeed()),
        name="wiki.feeds.recent_revisions",
    ),
    re_path(
        r"^feeds/(?P<format>[^/]+)/files/?",
        shared_cache_control(AttachmentsFeed()),
        name="attachments.feeds.recent_files",
    ),
]

lang_urlpatterns = non_document_patterns + [
    re_path(
        r"^(?P<document_path>%s)" % DOCUMENT_PATH_RE.pattern, include(document_patterns)
    ),
]
