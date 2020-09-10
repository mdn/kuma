import os
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.utils import IntegrityError
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_mysql.models import Model as MySQLModel
from storages.backends.s3boto3 import S3Boto3Storage

from .utils import attachment_upload_to, full_attachment_url


class AttachmentStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        configuration = dict(
            access_key=settings.ATTACHMENTS_AWS_ACCESS_KEY_ID,
            secret_key=settings.ATTACHMENTS_AWS_SECRET_ACCESS_KEY,
            bucket_name=settings.ATTACHMENTS_AWS_STORAGE_BUCKET_NAME,
            object_parameters={"CacheControl": "public, max-age=31536000, immutable"},
            default_acl="public-read",
            querystring_auth=False,
            custom_domain=settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN,
            secure_urls=settings.ATTACHMENTS_AWS_S3_SECURE_URLS,
            region_name=settings.ATTACHMENTS_AWS_S3_REGION_NAME,
            endpoint_url=settings.ATTACHMENTS_AWS_S3_ENDPOINT_URL,
        )
        configuration.update(kwargs)

        super(AttachmentStorage, self).__init__(*args, **configuration)


storage = AttachmentStorage() if settings.ATTACHMENTS_USE_S3 else None


class Attachment(models.Model):
    """
    An attachment which can be inserted into one or more wiki documents.

    There is no direct database-level relationship between attachments
    and documents; insertion of an attachment is handled through
    markup in the document.
    """

    current_revision = models.ForeignKey(
        "AttachmentRevision",
        null=True,
        blank=True,
        related_name="current_for+",
        on_delete=models.SET_NULL,
    )
    # These get filled from the current revision.
    title = models.CharField(max_length=255, db_index=True)

    # This is somewhat like the bookkeeping we do for Documents, but
    # is also slightly more permanent because storing this ID lets us
    # map from old MindTouch file URLs (which are based on the ID) to
    # new kuma file URLs.
    mindtouch_attachment_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource",
        null=True,
        blank=True,
        db_index=True,
    )
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    class Meta(object):
        permissions = (("disallow_add_attachment", "Cannot upload attachment"),)

    def __str__(self):
        return self.title

    def get_file_url(self):
        if self.current_revision is None:
            return ""

        return full_attachment_url(self.id, self.current_revision.filename)

    @cached_property
    def current_file_size(self):
        """
        Return the current revisions file size or None in case there is no
        current revision.
        """
        try:
            return self.current_revision.file.size
        except (OSError, AttributeError):
            return None

    def attach(self, document, user, revision):
        """
        When an attachment revision form is saved, this is used to attach
        the new attachment to the given document via an intermediate M2M
        model that stores some extra data like the user and the revision's
        filename.
        """
        # First let's see if there is already an intermediate object available
        # for the current attachment, a.k.a. this was a previous uploaded file
        DocumentAttachment = document.files.through
        try:
            document_attachment = DocumentAttachment.objects.get(file_id=self.pk)
        except document.files.through.DoesNotExist:
            # no previous uploads found, create a new document-attachment
            document_attachment = DocumentAttachment.objects.create(
                file=self,
                document=document,
                attached_by=user,
                name=revision.filename,
                is_original=True,
            )
        else:
            document_attachment.is_original = True
            document_attachment.attached_by = user
            document_attachment.name = revision.filename
            document_attachment.save()
        return document_attachment


class AttachmentRevision(models.Model):
    """
    A revision of an attachment.
    """

    DEFAULT_MIME_TYPE = "application/octet-stream"

    attachment = models.ForeignKey(
        Attachment, related_name="revisions", on_delete=models.CASCADE
    )

    file = models.FileField(
        storage=storage,
        upload_to=attachment_upload_to,
        max_length=500,
    )

    title = models.CharField(max_length=255, null=True, db_index=True)

    mime_type = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        default=DEFAULT_MIME_TYPE,
        help_text=_(
            "The MIME type is used when serving the attachment. "
            "Automatically populated by inspecting the file on "
            "upload. Please only override if needed."
        ),
    )
    # Does not allow wiki markup
    description = models.TextField(blank=True)

    created = models.DateTimeField(default=datetime.now)
    comment = models.CharField(max_length=255, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_attachment_revisions",
        on_delete=models.PROTECT,
    )
    is_approved = models.BooleanField(default=True, db_index=True)

    # As with document revisions, bookkeeping for the MindTouch
    # migration.
    #
    # TODO: Do we actually need full file revision history from
    # MindTouch?
    mindtouch_old_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource revision",
        null=True,
        blank=True,
        db_index=True,
        unique=True,
    )
    is_mindtouch_migration = models.BooleanField(
        default=False, db_index=True, help_text="Did this revision come from MindTouch?"
    )

    class Meta:
        verbose_name = _("attachment revision")
        verbose_name_plural = _("attachment revisions")

    def __str__(self):
        return '%s (file: "%s", ID: #%s)' % (self.title, self.filename, self.pk)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        super(AttachmentRevision, self).save(*args, **kwargs)
        if self.is_approved and (
            not self.attachment.current_revision
            or self.attachment.current_revision.id < self.id
        ):
            self.make_current()

    def delete(self, username=None, individual=True, *args, **kwargs):
        """
        Adds a check if the deletion was originally intended to be done
        individually or from a nested deletion when an attachment and all
        of its revisions was supposed to be deleted.

        individual == True means only the revision should be deleted and
        therefor the check if there are other sibling revisions is moot.
        """
        if individual and self.siblings().count() == 0:
            raise IntegrityError(
                "You cannot delete the last revision of "
                "attachment %s" % self.attachment
            )
        trash_item = self.trash(username=username)
        super(AttachmentRevision, self).delete(*args, **kwargs)
        return trash_item

    def trash(self, username=None):
        """
        Given an attachment revision instance and a request create a
        TrashedAttachment instance to record it being deleted.

        Then return the new trash item.
        """
        trashed_attachment = TrashedAttachment(
            file=self.file,
            trashed_by=username or "unknown",
            was_current=(
                self.attachment
                and self.attachment.current_revision
                and self.attachment.current_revision.pk == self.pk
            ),
        )
        trashed_attachment.save()
        return trashed_attachment

    def make_current(self):
        """Make this revision the current one for the attachment."""
        self.attachment.title = self.title
        self.attachment.current_revision = self
        self.attachment.save()

    def get_previous(self):
        return (
            self.attachment.revisions.filter(
                is_approved=True,
                created__lt=self.created,
            )
            .order_by("-created")
            .first()
        )

    def siblings(self):
        return self.attachment.revisions.exclude(pk=self.pk)


class TrashedAttachment(MySQLModel):

    file = models.FileField(
        storage=storage,
        upload_to=attachment_upload_to,
        max_length=500,
        help_text=_("The attachment file that was trashed"),
    )

    trashed_at = models.DateTimeField(
        default=datetime.now,
        help_text=_("The date and time the attachment was trashed"),
    )
    trashed_by = models.CharField(
        max_length=30,
        blank=True,
        help_text=_("The username of the user who trashed the attachment"),
    )

    was_current = models.BooleanField(
        default=False,
        help_text=_(
            "Whether or not this attachment was the current "
            "attachment revision at the time of trashing."
        ),
    )

    class Meta:
        verbose_name = _("Trashed attachment")
        verbose_name_plural = _("Trashed attachments")

    def __str__(self):
        return self.filename

    @property
    def filename(self):
        return os.path.basename(self.file.name)
