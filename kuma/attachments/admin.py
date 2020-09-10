from django.conf import settings
from django.contrib import admin, messages
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.text import get_text_list
from django.utils.translation import gettext_lazy as _

from kuma.core.admin import DisabledDeleteActionMixin
from kuma.core.urlresolvers import reverse

from .forms import AdminAttachmentRevisionForm
from .models import Attachment, AttachmentRevision, TrashedAttachment


class AttachmentRevisionInline(admin.StackedInline):
    model = AttachmentRevision
    extra = 1
    can_delete = False
    raw_id_fields = ["creator"]
    form = AdminAttachmentRevisionForm


@admin.register(Attachment)
class AttachmentAdmin(DisabledDeleteActionMixin, admin.ModelAdmin):
    fields = ["current_revision", "mindtouch_attachment_id"]
    list_display = ["id", "title", "modified", "full_url"]
    list_display_links = ["id", "title"]
    list_filter = [
        "modified",
        "current_revision__is_approved",
        "current_revision__mime_type",
    ]
    list_select_related = ["current_revision"]
    ordering = ["-modified"]
    search_fields = ["title"]
    raw_id_fields = ["current_revision"]
    date_hierarchy = "modified"
    inlines = [AttachmentRevisionInline]

    def full_url(self, obj):
        url = obj.get_file_url()
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>', url, url
        )

    full_url.short_description = "Full URL"

    def delete_revisions(self, request, revisions):
        # go through all revisions and trash them,
        # they'll actually be deleted by the deletion of the attachment
        trashed_attachments = []
        for revision in revisions:
            trashed_attachment = revision.delete(
                username=request.user.username,
                individual=False,
            )
            trashed_attachments.append(trashed_attachment)
        if trashed_attachments:
            self.message_user(
                request,
                _(
                    "The following attachment files were moved to the trash: "
                    "%(filenames)s. You may want to review them before their "
                    "automatic purge after %(days)s days from the file "
                    "storage."
                )
                % {
                    "filenames": get_text_list(trashed_attachments, _("and")),
                    "days": settings.WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS,
                },
                messages.SUCCESS,
            )
        return trashed_attachments

    def delete_model(self, request, obj):
        self.delete_revisions(request, obj.revisions.all().iterator())
        # call the actual deletion of the attachment object
        super(AttachmentAdmin, self).delete_model(request, obj)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        self.delete_revisions(request, formset.deleted_objects)
        for instance in instances:
            instance.creator = request.user
            instance.save()
        formset.save_m2m()


@admin.register(AttachmentRevision)
class AttachmentRevisionAdmin(DisabledDeleteActionMixin, admin.ModelAdmin):
    fields = ["attachment", "file", "title", "mime_type", "description", "is_approved"]
    list_display = [
        "id",
        "title",
        "created",
        "mime_type",
        "is_approved",
        "attachment_url",
    ]
    list_display_links = ["id", "title"]
    list_editable = ["is_approved"]
    list_filter = ["created", "is_approved", "mime_type"]
    ordering = ["-created"]
    search_fields = ["title", "description", "creator__username"]
    raw_id_fields = ["attachment"]
    date_hierarchy = "created"
    list_select_related = ["creator"]
    form = AdminAttachmentRevisionForm

    def attachment_url(self, obj):
        attachment = obj.attachment
        url = reverse("admin:attachments_attachment_change", args=(attachment.pk,))
        return format_html('<a href="{}">{}</a>', url, attachment.pk)

    attachment_url.short_description = "Attachment"

    def save_model(self, request, obj, form, change):
        obj.creator = request.user
        obj.save()

    def has_delete_permission(self, request, obj=None):
        """
        Disable deletion of individual Documents, by always returning
        False for the permission check.
        """
        if obj is None:
            return super(AttachmentRevisionAdmin, self).has_delete_permission(
                request, obj
            )
        else:
            return obj.siblings().count() != 0

    def delete_model(self, request, obj):
        # call the actual deletion of the attachment revision object
        # that also creates a trash item
        trash_item = obj.delete(username=request.user.username)
        self.message_user(
            request,
            _(
                'The attachment file "%(filename)s" was moved to the trash. '
                "You may want to review the file before its automatic purge "
                "after %(days)s days from the file storage system."
            )
            % {
                "filename": force_text(trash_item.filename),
                "days": settings.WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS,
            },
            messages.SUCCESS,
        )


@admin.register(TrashedAttachment)
class TrashedAttachmentAdmin(DisabledDeleteActionMixin, admin.ModelAdmin):
    list_display = ["file", "trashed_at", "trashed_by", "was_current"]
    list_filter = ["trashed_at", "was_current"]
    search_fields = ["file"]
    date_hierarchy = "trashed_at"
    readonly_fields = ["file", "trashed_at", "trashed_by", "was_current"]
