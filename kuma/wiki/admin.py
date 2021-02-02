from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html, format_html_join

from kuma.core.admin import DisabledDeletionMixin
from kuma.core.urlresolvers import reverse

from .models import (
    Document,
    DocumentDeletionLog,
    DocumentTag,
    EditorToolbar,
    Revision,
)


def related_revisions_link(obj):
    """HTML link to related revisions for admin change list"""
    link = "%s?%s" % (
        reverse("admin:wiki_revision_changelist", args=[]),
        "document__exact=%s" % (obj.id),
    )
    count = obj.revisions.count()
    what = (count == 1) and "revision" or "revisions"
    return format_html('<a href="{}">{}&nbsp;{}</a>', link, count, what)


related_revisions_link.short_description = "All Revisions"


def current_revision_link(obj):
    """HTML link to the current revision for the admin change list"""
    if not obj.current_revision:
        return "None"
    rev = obj.current_revision
    rev_url = reverse("admin:wiki_revision_change", args=[rev.id])
    return format_html(
        '<a href="{}">Current&nbsp;Revision&nbsp;(#{})</a>', rev_url, rev.id
    )


current_revision_link.short_description = "Current Revision"


def parent_document_link(obj):
    """HTML link to the topical parent document for admin change list"""
    if not obj.parent:
        return ""
    url = reverse("admin:wiki_document_change", args=[obj.parent.id])
    return format_html(
        '<a href="{}">Translated&nbsp;from&nbsp;(#{})</a>', url, obj.parent.id
    )


parent_document_link.short_description = "Translation Parent"


def topic_parent_document_link(obj):
    """HTML link to the parent document for admin change list"""
    if not obj.parent_topic:
        return ""
    url = reverse("admin:wiki_document_change", args=[obj.parent_topic.id])
    return format_html(
        '<a href="{}">Topic&nbsp;Parent&nbsp;(#{})</a>', url, obj.parent_topic.id
    )


topic_parent_document_link.short_description = "Parent Document"


def topic_children_documents_link(obj):
    """HTML link to a list of child documents"""
    count = obj.children.count()
    if not count:
        return ""
    link = "%s?%s" % (
        reverse("admin:wiki_document_changelist", args=[]),
        "parent_topic__exact=%s" % (obj.id),
    )
    what = "child" if count == 1 else "children"
    return format_html('<a href="{}">{}&nbsp;{}</a>', link, count, what)


topic_children_documents_link.short_description = "Child Documents"


def topic_sibling_documents_link(obj):
    """HTML link to a list of sibling documents"""
    if not obj.parent_topic:
        return ""
    count = obj.parent_topic.children.count()
    if not count:
        return ""
    link = "%s?%s" % (
        reverse("admin:wiki_document_changelist", args=[]),
        "parent_topic__exact=%s" % (obj.parent_topic.id),
    )
    what = "sibling" if count == 1 else "siblings"
    return format_html('<a href="{}">{}&nbsp;{}</a>', link, count, what)


topic_sibling_documents_link.short_description = "Sibling Documents"


def document_link(obj):
    """Public link to the document"""
    link = obj.get_absolute_url()
    return format_html(
        '<a target="_blank" rel="noopener" href="{}"><img src="{}img/icons/link_external.png"> View</a>',
        link,
        settings.STATIC_URL,
    )


document_link.short_description = "Public"


def combine_funcs(obj, funcs):
    """Combine several field functions into one block of lines"""
    items = (func(obj) for func in funcs)
    list_body = format_html_join("", "<li>{}</li>", ([item] for item in items if item))
    return format_html("<ul>{}</ul>", list_body)


def document_nav_links(obj):
    """Combine the document hierarchy nav links"""
    return combine_funcs(
        obj,
        (
            parent_document_link,
            topic_parent_document_link,
            topic_sibling_documents_link,
            topic_children_documents_link,
        ),
    )


document_nav_links.short_description = "Hierarchy"


def revision_links(obj):
    """Combine the revision nav links"""
    return combine_funcs(
        obj,
        (
            current_revision_link,
            related_revisions_link,
        ),
    )


revision_links.short_description = "Revisions"


def rendering_info(obj):
    """Combine the rendering times into one block"""
    items = (
        format_html(template, *data)
        for (template, data) in (
            (
                '<img src="{}admin/img/icon-{}.svg" alt="{}"> Deferred rendering',
                [
                    settings.STATIC_URL,
                    "yes" if obj.defer_rendering else "no",
                    obj.defer_rendering,
                ],
            ),
            ("{} (last)", [obj.last_rendered_at]),
            ("{} (started)", [obj.render_started_at]),
            ("{} (scheduled)", [obj.render_scheduled_at]),
        )
        if any(data)
    )

    list_body = format_html_join("", "<li>{}</li>", ([item] for item in items))
    return format_html("<ul>{}</ul>", list_body)


rendering_info.short_description = "Rendering"
rendering_info.admin_order_field = "last_rendered_at"


@admin.register(Document)
class DocumentAdmin(DisabledDeletionMixin, admin.ModelAdmin):
    class Media:
        js = ("js/wiki-admin.js",)

    list_per_page = 25
    actions = ()
    fieldsets = (
        (None, {"fields": ("locale", "title")}),
        (
            "Rendering",
            {"fields": ("defer_rendering", "render_expires", "render_max_age")},
        ),
        ("Topical Hierarchy", {"fields": ("parent_topic",)}),
        (
            "Localization",
            {
                "description": "The document should be <strong>either</strong> "
                "localizable, <strong>or</strong> have a parent - "
                "never both.",
                "fields": ("is_localizable", "parent"),
            },
        ),
    )
    list_display = (
        "id",
        "locale",
        "slug",
        "title",
        document_link,
        "modified",
        "render_expires",
        "render_max_age",
        rendering_info,
        document_nav_links,
        revision_links,
    )
    list_display_links = (
        "id",
        "slug",
    )
    list_filter = ("defer_rendering", "is_localizable", "locale", "deleted")
    raw_id_fields = (
        "parent",
        "parent_topic",
    )
    readonly_fields = ("id", "current_revision")
    search_fields = ("title", "slug", "html", "current_revision__tags")

    def get_queryset(self, request):
        """
        The Document class has multiple managers which perform
        different filtering based on deleted status; we want the
        special admin-only one that doesn't filter.
        """
        return Document.admin_objects.all()


@admin.register(DocumentDeletionLog)
class DocumentDeletionLogAdmin(DisabledDeletionMixin, admin.ModelAdmin):
    list_display = ["slug", "locale", "user", "timestamp"]
    list_filter = ["timestamp", "locale"]
    search_fields = ["slug", "reason"]
    ordering = ["-timestamp"]
    readonly_fields = ["locale", "slug", "user", "timestamp"]


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    fields = (
        "title",
        "summary",
        "content",
        "keywords",
        "tags",
        "comment",
        "is_approved",
    )
    list_display = ("id", "slug", "title", "is_approved", "created", "creator")
    list_display_links = ("id", "slug")
    list_filter = ("is_approved",)
    ordering = ("-created",)
    search_fields = ("title", "slug", "summary", "content", "tags")


@admin.register(EditorToolbar)
class EditorToolbarAdmin(admin.ModelAdmin):
    list_display = ["name", "creator", "default"]
    list_filters = ["default"]
    raw_id_fields = ["creator"]
