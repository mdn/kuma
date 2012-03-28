from django.contrib import admin

from wiki.models import Document, Revision, EditorToolbar


class DocumentAdmin(admin.ModelAdmin):
    fields = ('title', 'slug', 'locale', 'parent', 'category')
    list_display = ('id', 'locale', 'slug', 'title', 'is_localizable',
                    'modified', 'parent_document_link',
                    'current_revision_link', 'related_revisions_link',)
    list_display_links = ('id', 'slug',)
    list_filter = ('is_template', 'is_localizable', 'category', 'locale')
    raw_id_fields = ('parent',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title', 'slug', 'html')


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
