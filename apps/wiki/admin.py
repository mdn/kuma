from datetime import datetime

from django.contrib import admin
from django.http import HttpResponse

from sumo.urlresolvers import reverse

from wiki.models import (Document, DocumentZone, DocumentTag, Revision,
                         EditorToolbar, Attachment, AttachmentRevision)


def dump_selected_documents(self, request, queryset):
    filename = "documents_%s.json" % (datetime.now().isoformat(),)
    response = HttpResponse(mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    Document.objects.dump_json(queryset, response)
    return response

dump_selected_documents.short_description = "Dump selected documents as JSON"


def repair_breadcrumbs(self, request, queryset):
    for doc in queryset:
        doc.repair_breadcrumbs()
repair_breadcrumbs.short_description = "Repair translation breadcrumbs"


def enable_deferred_rendering_for_documents(self, request, queryset):
    queryset.update(defer_rendering=True)
    self.message_user(request, 'Enabled deferred rendering for %s Documents' %
                               queryset.count())
enable_deferred_rendering_for_documents.short_description = (
    "Enable deferred rendering for selected documents")


def disable_deferred_rendering_for_documents(self, request, queryset):
    queryset.update(defer_rendering=False)
    self.message_user(request, 'Disabled deferred rendering for %s Documents' %
                               queryset.count())
disable_deferred_rendering_for_documents.short_description = (
    "Disable deferred rendering for selected documents")


def force_render_documents(self, request, queryset):
    count, bad_count = 0, 0
    for doc in queryset:
        try:
            doc.render(cache_control='no-cache')
            count += 1
        except:
            bad_count += 1
            pass
    self.message_user(request, "Rendered %s documents, failed on %s "
                               "documents." % (count, bad_count))
force_render_documents.short_description = (
    "Perform rendering for selected documents")


def resave_current_revision(self, request, queryset):
    count, bad_count = 0, 0
    for doc in queryset:
        if not doc.current_revision:
            bad_count += 1
        else:
            doc.current_revision.save()
            count += 1
    self.message_user(request, "Resaved current revision for %s documents. %s "
                               "documents had no current revision." %
                               (count, bad_count))

resave_current_revision.short_description = (
    "Re-save current revision for selected documents")


def related_revisions_link(self):
    """HTML link to related revisions for admin change list"""
    link = '%s?%s' % (
        reverse('admin:wiki_revision_changelist', args=[]),
        'document__exact=%s' % (self.id)
    )
    count = self.revisions.count()
    what = (count == 1) and 'revision' or 'revisions'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

related_revisions_link.allow_tags = True
related_revisions_link.short_description = "All Revisions"


def current_revision_link(self):
    """HTML link to the current revision for the admin change list"""
    if not self.current_revision:
        return "None"
    rev = self.current_revision
    rev_url = reverse('admin:wiki_revision_change', args=[rev.id])
    return '<a href="%s">Current&nbsp;Revision&nbsp;(#%s)</a>' % (rev_url, rev.id)

current_revision_link.allow_tags = True
current_revision_link.short_description = "Current Revision"


def parent_document_link(self):
    """HTML link to the topical parent document for admin change list"""
    if not self.parent:
        return ''
    url = reverse('admin:wiki_document_change', args=[self.parent.id])
    return '<a href="%s">Translated&nbsp;from&nbsp;(#%s)</a>' % (url, self.parent.id)

parent_document_link.allow_tags = True
parent_document_link.short_description = "Translation Parent"


def topic_parent_document_link(self):
    """HTML link to the parent document for admin change list"""
    if not self.parent_topic:
        return ''
    url = reverse('admin:wiki_document_change',
                  args=[self.parent_topic.id])
    return '<a href="%s">Topic&nbsp;Parent&nbsp;(#%s)</a>' % (url, self.parent_topic.id)

topic_parent_document_link.allow_tags = True
topic_parent_document_link.short_description = "Parent Document"


def topic_children_documents_link(self):
    """HTML link to a list of child documents"""
    count = self.children.count()
    if not count:
        return ''
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (self.id)
    )
    what = (count == 1) and 'child' or 'children'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

topic_children_documents_link.allow_tags = True
topic_children_documents_link.short_description = "Child Documents"


def topic_sibling_documents_link(self):
    """HTML link to a list of sibling documents"""
    count = self.parent_topic.children.count()
    if not count:
        return ''
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (self.parent_topic.id)
    )
    what = (count == 1) and 'sibling' or 'siblings'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

topic_sibling_documents_link.allow_tags = True
topic_sibling_documents_link.short_description = "Sibling Documents"


def document_link(self):
    """Public link to the document"""
    link = self.get_absolute_url()
    return ('<a target="_blank" href="%s">'
            '<img src="/media/img/icons/link_external.png"> View</a>' %
            (link,))

document_link.allow_tags = True
document_link.short_description = "Public"


def combine_funcs(self, funcs):
    """Combine several field functions into one block of lines"""
    out = (x(self) for x in funcs)
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % x for x in out if x)


def document_nav_links(self):
    """Combine the document hierarchy nav links"""
    return combine_funcs(self, (
        parent_document_link,
        topic_parent_document_link,
        topic_sibling_documents_link,
        topic_children_documents_link,
    ))

document_nav_links.allow_tags = True
document_nav_links.short_description = "Hierarchy"


def revision_links(self):
    """Combine the revision nav links"""
    return combine_funcs(self, (
        current_revision_link,
        related_revisions_link,
    ))

revision_links.allow_tags = True
revision_links.short_description = "Revisions"


def rendering_info(self):
    """Combine the rendering times into one block"""
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % (x % y) for x, y in (
        ('<img src="/admin-media/img/admin/icon-yes.gif" alt="%s"> '
         'Deferred rendering', self.defer_rendering),
        ('%s (last)',        self.last_rendered_at),
        ('%s (started)',     self.render_started_at),
        ('%s (scheduled)',   self.render_scheduled_at),
    ) if y)

rendering_info.allow_tags = True
rendering_info.short_description = 'Rendering'
rendering_info.admin_order_field = 'last_rendered_at'


def current_revision_reviewed(self):
    return self.current_revision.reviewed
current_revision_reviewed.admin_order_field = 'current_revision__reviewed'


class DocumentAdmin(admin.ModelAdmin):

    class Media:
        js = ('js/wiki-admin.js',)

    list_per_page = 25
    actions = (dump_selected_documents,
               resave_current_revision,
               force_render_documents,
               enable_deferred_rendering_for_documents,
               disable_deferred_rendering_for_documents,
               repair_breadcrumbs)
    change_list_template = 'admin/wiki/document/change_list.html'
    fields = ('locale', 'title', 'defer_rendering', 'parent',
              'parent_topic', 'category',)
    list_display = ('id', 'locale', 'slug', 'title',
                    document_link,
                    'modified',
                    # HACK: This is temporary, just to help us see & sort
                    # documents by an empty reviewed field on current revision.
                    # This is symptomatic of a migration issue, and this field
                    # should be removed from the admin list after bug 769129 is
                    # resolved.
                    current_revision_reviewed,
                    rendering_info,
                    document_nav_links,
                    revision_links,)
    list_display_links = ('id', 'slug',)
    list_filter = ('defer_rendering', 'is_template', 'is_localizable',
                   'category', 'locale')
    raw_id_fields = ('parent', 'parent_topic',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title', 'slug', 'html', 'current_revision__tags')


class RevisionAdmin(admin.ModelAdmin):
    fields = ('title', 'summary', 'content', 'keywords', 'tags',
              'reviewed', 'comment', 'is_approved')
    list_display = ('id', 'slug', 'title', 'is_approved', 'created',
                    'creator',)
    list_display_links = ('id', 'slug')
    list_filter = ('is_approved', )
    ordering = ('-created',)
    search_fields = ('title', 'slug', 'summary', 'content', 'tags')


class AttachmentAdmin(admin.ModelAdmin):
    fields = ('current_revision', 'mindtouch_attachment_id')
    list_display = ('title', 'slug', 'modified', 'mindtouch_attachment_id')
    ordering = ('title',)
    search_fields = ('title',)


class AttachmentRevisionAdmin(admin.ModelAdmin):
    fields = ('attachment', 'file', 'title', 'slug',
              'mime_type', 'description', 'is_approved')
    list_display = ('title', 'created')
    ordering = ('-created', 'title')
    search_fields = ('title', 'description')


class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    ordering = ('name',)


class DocumentZoneAdmin(admin.ModelAdmin):
    raw_id_fields = ('document',)


admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentZone, DocumentZoneAdmin)
admin.site.register(DocumentTag, DocumentTagAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(EditorToolbar, admin.ModelAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(AttachmentRevision, AttachmentRevisionAdmin)
