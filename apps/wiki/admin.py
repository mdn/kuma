from datetime import datetime

from django.contrib import admin
from django.core import serializers
from django.http import HttpResponse
from django.core import serializers

from sumo.urlresolvers import reverse, split_path

from wiki.models import (Document, Revision, EditorToolbar,
                         Attachment, AttachmentRevision)


def dump_selected_documents(self, request, queryset):
    filename = "documents_%s.json" % (datetime.now().isoformat(),)
    response = HttpResponse(mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    Document.objects.dump_json(queryset, response) 
    return response

dump_selected_documents.short_description = "Dump selected documents as JSON"


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


def related_revisions_link(self):
    """HTML link to related revisions for admin change list"""
    link = '%s?%s' % (
        reverse('admin:wiki_revision_changelist', args=[]),
        'document__exact=%s' % (self.id)
    )
    count = self.revisions.count()
    what = (count == 1) and 'revision' or 'revisions'
    return '<a href="%s">%s %s</a>' % (link, count, what)

related_revisions_link.allow_tags = True
related_revisions_link.short_description = "All Revisions"


def current_revision_link(self):
    """HTML link to the current revision for the admin change list"""
    if not self.current_revision:
        return "None"
    rev = self.current_revision
    rev_url = reverse('admin:wiki_revision_change', args=[rev.id])
    return '<a href="%s">Revision #%s</a>' % (rev_url, rev.id)

current_revision_link.allow_tags = True
current_revision_link.short_description = "Current Revision"


def parent_document_link(self):
    """HTML link to the topical parent document for admin change list"""
    if not self.parent:
        return "None"
    url = reverse('admin:wiki_document_change', args=[self.parent.id])
    return '<a href="%s">Document #%s</a>' % (url, self.parent.id)

parent_document_link.allow_tags = True
parent_document_link.short_description = "Translation Parent"


def topic_parent_document_link(self):
    """HTML link to the parent document for admin change list"""
    if not self.parent_topic:
        return "None"
    url = reverse('admin:wiki_document_change',
                  args=[self.parent_topic.id])
    return '<a href="%s">Document #%s</a>' % (url, self.parent_topic.id)

topic_parent_document_link.allow_tags = True
topic_parent_document_link.short_description = "Parent Document"


def topic_children_documents_link(self):
    """HTML link to a list of child documents"""
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (self.id)
    )
    count = self.children.count()
    what = (count == 1) and 'document' or 'documents'
    return '<a href="%s">%s %s</a>' % (link, count, what)

topic_children_documents_link.allow_tags = True
topic_children_documents_link.short_description = "Child Documents"


def topic_sibling_documents_link(self):
    """HTML link to a list of sibling documents"""
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (self.parent_topic.id)
    )
    count = self.parent_topic.children.count()
    what = (count == 1) and 'document' or 'documents'
    return '<a href="%s">%s %s</a>' % (link, count, what)

topic_sibling_documents_link.allow_tags = True
topic_sibling_documents_link.short_description = "Sibling Documents"


def document_link(self):
    link = self.get_absolute_url()
    return '<a target="_blank" href="%s">Link</a>' % (link,)

document_link.allow_tags = True
document_link.short_description = "Public Link"


class DocumentAdmin(admin.ModelAdmin):
    list_per_page = 50
    actions = (dump_selected_documents,
               enable_deferred_rendering_for_documents,
               disable_deferred_rendering_for_documents)
    change_list_template = 'admin/wiki/document/change_list.html'
    fields = ('locale', 'slug', 'title', 'defer_rendering', 'parent',
              'parent_topic', 'category')
    list_display = ('id', 'slug', 'locale', 'title',
                    document_link,
                    'defer_rendering',
                    'is_localizable', 'modified', 
                    'last_rendered_at', 
                    'render_started_at', 
                    'render_scheduled_at',
                    parent_document_link,
                    topic_parent_document_link,
                    topic_sibling_documents_link,
                    topic_children_documents_link,
                    current_revision_link,
                    related_revisions_link,)
    list_display_links = ('id', 'slug',)
    list_filter = ('defer_rendering', 'is_template', 'is_localizable',
                   'category', 'locale')
    raw_id_fields = ('parent', 'parent_topic',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title', 'slug', 'html', 'current_revision__tags')


class RevisionAdmin(admin.ModelAdmin):
    fields = ('title', 'slug', 'summary', 'content', 'keywords', 'tags',
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


admin.site.register(Document, DocumentAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(EditorToolbar, admin.ModelAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(AttachmentRevision, AttachmentRevisionAdmin)
