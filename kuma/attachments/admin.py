from django.contrib import messages
from django.contrib import admin
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.text import get_text_list
from django.utils.translation import ugettext_lazy as _

from constance import config

from .forms import AdminAttachmentRevisionForm
from .models import Attachment, AttachmentRevision, TrashedAttachment


class AttachmentRevisionInline(admin.StackedInline):
    model = AttachmentRevision
    extra = 1
    can_delete = False
    raw_id_fields = ['creator']
    form = AdminAttachmentRevisionForm


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    actions = None
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

    def on_attachment_delete(self, **kwargs):
        """
        Signal handle to be called when an attachment is deleted
        """
        instance = kwargs.get('instance', None)
        if instance is not None:
            for revision in instance.revisions.all():
                revision.trash()

    def delete_model(self, request, obj):
        # go through all revisions and trash them,
        # they'll actually be deleted by the deletion of the attachment
        trash = []
        for revision in obj.revisions.all():
            trash_item = revision.trash(username=request.user.username)
            trash.append(trash_item)
        if trash:
            self.message_user(
                request,
                _('The following attachment files were moved to the trash: '
                  '%(filenames)s. You may want to review them before their '
                  'automatic purge after %(days)s days from the file '
                  'storage.') %
                {'filenames': get_text_list(trash, _('and')),
                 'days': config.WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS},
                messages.SUCCESS)
        # call the actual deletion of the attachment object
        super(AttachmentAdmin, self).delete_model(request, obj)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        # go through all files and see if there
        trash = []
        for obj in formset.deleted_objects:
            if isinstance(obj, AttachmentRevision):
                trash_item = obj.delete(username=request.user.username)
                trash.append(trash_item)
            else:
                obj.delete()
        if trash:
            self.message_user(
                request,
                _('The following attachment files were moved to the trash: '
                  '%(filenames)s. You may want to review them before their '
                  'automatic purge after %(days)s days from the file '
                  'storage.') %
                {'filenames': get_text_list(trash, _('and')),
                 'days': config.WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS},
                messages.SUCCESS)

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

    def delete_model(self, request, obj):
        # call the actual deletion of the attachment revision object
        # that also creates a trash item
        trash_item = obj.delete(username=request.user.username)
        self.message_user(
            request,
            _('The attachment file "%(filename)s" was moved to the trash. '
              'You may want to review the file before its automatic purge '
              'after %(days)s days from the file storage system.') % {
                'filename': force_text(trash_item.filename),
                'days': config.WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS,
            }, messages.SUCCESS)


@admin.register(TrashedAttachment)
class TrashedAttachmentAdmin(admin.ModelAdmin):
    list_display = ['file', 'trashed_at', 'trashed_by', 'was_current']
    list_filter = ['trashed_at', 'was_current']
    search_fields = ['file']
    date_hierarchy = 'trashed_at'
    readonly_fields = ['file', 'trashed_at', 'trashed_by', 'was_current']
