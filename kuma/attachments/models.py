from datetime import datetime

from django.conf import settings
from django.db import models

import jingo

from .managers import AttachmentManager
from .utils import attachment_upload_to, full_attachment_url


class Attachment(models.Model):
    """
    An attachment which can be inserted into one or more wiki documents.

    There is no direct database-level relationship between attachments
    and documents; insertion of an attachment is handled through
    markup in the document.
    """
    class Meta(object):
        permissions = (
            ("disallow_add_attachment", "Cannot upload attachment"),
        )

    objects = AttachmentManager()

    current_revision = models.ForeignKey('AttachmentRevision', null=True,
                                         related_name='current_rev')

    # These get filled from the current revision.
    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # This is somewhat like the bookkeeping we do for Documents, but
    # is also slightly more permanent because storing this ID lets us
    # map from old MindTouch file URLs (which are based on the ID) to
    # new kuma file URLs.
    mindtouch_attachment_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource",
        null=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    @models.permalink
    def get_absolute_url(self):
        return ('attachments.attachment_detail', (), {'attachment_id': self.id})

    def get_file_url(self):
        return full_attachment_url(self.id, self.current_revision.filename())

    def attach(self, document, user, name):
        if self.id not in document.attachments.values_list('id', flat=True):
            from kuma.wiki.models import DocumentAttachment
            intermediate = DocumentAttachment(file=self,
                                              document=document,
                                              attached_by=user,
                                              name=name)
            intermediate.save()

    def get_embed_html(self):
        """
        Return suitable initial HTML for embedding this file in an
        article, generated from a template.

        The template searching is from most specific to least
        specific, based on mime-type. For example, an attachment with
        mime-type 'image/png' will try to load the following
        templates, in order, and use the first one found:

        * attachments/attachments/image_png.html

        * attachments/attachments/image.html

        * attachments/attachments/generic.html
        """
        rev = self.current_revision
        env = jingo.get_env()
        t = env.select_template([
            'attachments/attachments/%s.html' % rev.mime_type.replace('/', '_'),
            'attachments/attachments/%s.html' % rev.mime_type.split('/')[0],
            'attachments/attachments/generic.html'])
        return t.render({'attachment': rev})


class AttachmentRevision(models.Model):
    """
    A revision of an attachment.
    """
    attachment = models.ForeignKey(Attachment, related_name='revisions')

    file = models.FileField(upload_to=attachment_upload_to, max_length=500)

    title = models.CharField(max_length=255, null=True, db_index=True)
    slug = models.CharField(max_length=255, null=True, db_index=True)

    # This either comes from the MindTouch import or, for new files,
    # from the (as-yet-unwritten) upload view using the Python
    # mimetypes library to figure it out.
    #
    # TODO: do we want to make this an explicit set of choices? That'd
    # rule out certain types of attachments, but might be a lot safer.
    mime_type = models.CharField(max_length=255, db_index=True)

    description = models.TextField(blank=True)  # Does not allow wiki markup

    created = models.DateTimeField(default=datetime.now)
    comment = models.CharField(max_length=255, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name='created_attachment_revisions')
    is_approved = models.BooleanField(default=True, db_index=True)

    # As with document revisions, bookkeeping for the MindTouch
    # migration.
    #
    # TODO: Do we actually need full file revision history from
    # MindTouch?
    mindtouch_old_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource revision",
        null=True, db_index=True, unique=True)
    is_mindtouch_migration = models.BooleanField(
        default=False, db_index=True,
        help_text="Did this revision come from MindTouch?")

    def filename(self):
        return self.file.path.split('/')[-1]

    def save(self, *args, **kwargs):
        super(AttachmentRevision, self).save(*args, **kwargs)
        if self.is_approved and (
                not self.attachment.current_revision or
                self.attachment.current_revision.id < self.id):
            self.make_current()

    def make_current(self):
        """Make this revision the current one for the attachment."""
        self.attachment.title = self.title
        self.attachment.slug = self.slug
        self.attachment.current_revision = self
        self.attachment.save()

    def get_previous(self):
        previous_revisions = self.attachment.revisions.filter(
            is_approved=True,
            created__lt=self.created,
        ).order_by('-created')
        if len(previous_revisions):
            return previous_revisions[0]
