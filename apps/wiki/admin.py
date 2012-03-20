from datetime import datetime

from django.contrib import admin
from django.core import serializers
from django.http import HttpResponse

from smuggler.settings import SMUGGLER_FORMAT
from smuggler.utils import serialize_to_response

from wiki.models import Document, Revision, EditorToolbar


def dump_selected(modeladmin, request, queryset):
    objects = []
    for doc in queryset.all():
        rev = Revision.objects.get(id=doc.current_revision.id)
        doc.current_revision = None
        objects.append(doc)
        objects.append(rev)
    serializers.get_serializer('json')
    filename = "documents_%s.%s" % (
        datetime.now().isoformat(), SMUGGLER_FORMAT)
    response = HttpResponse(mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return serialize_to_response(objects, response)

dump_selected.short_description = "Dump selected objects as JSON data"


class DocumentAdmin(admin.ModelAdmin):
    actions = [dump_selected, ]
    change_list_template = 'admin/wiki/document/change_list.html'
    exclude = ('tags',)
    list_display = ('id', 'locale', 'slug', 'title', 'category',
                    'is_localizable')
    list_display_links = ('id', 'slug',)
    list_filter = ('is_template', 'is_localizable', 'category', 'locale')
    raw_id_fields = ('parent',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title',)


admin.site.register(Document, DocumentAdmin)
admin.site.register(Revision, admin.ModelAdmin)
admin.site.register(EditorToolbar, admin.ModelAdmin)
