from datetime import datetime

from django.contrib import admin
from django.core import serializers
from django.http import HttpResponse
from django.core import serializers

from wiki.models import Document, Revision, EditorToolbar


def dump_selected_documents(modeladmin, request, queryset):
    filename = "documents_%s.json" % (datetime.now().isoformat(),)
    response = HttpResponse(mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    Document.objects.dump_json(queryset, response) 
    return response

dump_selected_documents.short_description = "Dump selected documents as JSON"


class DocumentAdmin(admin.ModelAdmin):
    actions = [dump_selected_documents, ]
    change_list_template = 'admin/wiki/document/change_list.html'
    fields = ('title', 'slug', 'locale', 'parent', 'parent_topic', 'category')
    list_display = ('id', 'locale', 'slug', 'title', 'is_localizable',
                    'modified', 'parent_document_link',
                    'topic_parent_document_link',
                    'current_revision_link', 'related_revisions_link',)
    list_display_links = ('id', 'slug',)
    list_filter = ('is_template', 'is_localizable', 'category', 'locale')
    raw_id_fields = ('parent',)
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


admin.site.register(Document, DocumentAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(EditorToolbar, admin.ModelAdmin)
