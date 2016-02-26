from django.apps import AppConfig
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _


class AttachmentsConfig(AppConfig):
    """
    The Django App Config class to store information about the users app
    and do startup time things.
    """
    name = 'kuma.attachments'
    verbose_name = _('Attachments')

    def ready(self):
        super(AttachmentsConfig, self).ready()

        TrashedAttachment = self.get_model('TrashedAttachment')
        signals.pre_delete.connect(self.on_trash_delete,
                                   sender=TrashedAttachment,
                                   dispatch_uid='attachments.trash.delete')

        AttachmentRevision = self.get_model('AttachmentRevision')
        signals.post_delete.connect(self.after_revision_delete,
                                    sender=AttachmentRevision,
                                    dispatch_uid='attachments.revision.delete')

    def after_revision_delete(self, **kwargs):
        """
        Signal handler to be called when an attachment revision is deleted
        """
        instance = kwargs.get('instance', None)
        if instance is not None:
            # see if there is a previous revision
            previous = instance.get_previous()
            # if yes, make it the current revision of the attachment
            if previous is not None:
                previous.make_current()

    def on_trash_delete(self, **kwargs):
        """
        Signal handler to be called when a trash item is deleted.
        """
        instance = kwargs.get('instance', None)
        if instance is not None:
            # if a file entry is present, delete the file with the storage
            # without saving the model instance
            if instance.file:
                instance.file.delete(save=False)
