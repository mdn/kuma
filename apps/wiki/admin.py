from django.contrib import admin

from wiki.models import Document, Revision


class DocumentAdmin(admin.ModelAdmin):
    exclude = ('tags',)
    list_display = ('locale', 'title', 'category', 'is_localizable')
    list_display_links = ('title',)
    list_filter = ('is_template', 'is_localizable', 'category', 'locale')
    raw_id_fields = ('parent',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title',)

class RevisionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Document, DocumentAdmin)
admin.site.register(Revision, RevisionAdmin)
