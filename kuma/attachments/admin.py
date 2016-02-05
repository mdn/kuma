from django.contrib import admin
from django.utils.html import format_html

from .forms import AdminAttachmentRevisionForm
from .models import Attachment, AttachmentRevision


class AttachmentRevisionInline(admin.StackedInline):
    model = AttachmentRevision
    extra = 1
    can_delete = False
    raw_id_fields = ['creator']
    form = AdminAttachmentRevisionForm


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    fields = ['current_revision', 'mindtouch_attachment_id']
    list_display = ['title', 'modified', 'full_url', 'mindtouch_attachment_id']
    list_filter = ['modified']
    ordering = ['-modified']
    search_fields = ['title']
    raw_id_fields = ['current_revision']
    date_hierarchy = 'modified'
    inlines = [
        AttachmentRevisionInline,
    ]

    def full_url(self, obj):
        url = obj.get_file_url()
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    full_url.short_description = 'Full URL'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.creator = request.user
            instance.save()
        formset.save_m2m()


@admin.register(AttachmentRevision)
class AttachmentRevisionAdmin(admin.ModelAdmin):
    fields = ['attachment', 'file', 'title', 'mime_type', 'description',
              'is_approved']
    list_display = ['title', 'created', 'mime_type', 'is_approved']
    list_editable = ['is_approved']
    list_filter = ['created', 'is_approved', 'mime_type']
    ordering = ['-created', 'title']
    search_fields = ['title', 'description', 'creator__username']
    raw_id_fields = ['attachment']
    date_hierarchy = 'created'
    list_select_related = ['creator']
    form = AdminAttachmentRevisionForm

    def save_model(self, request, obj, form, change):
        obj.creator = request.user
        obj.save()
