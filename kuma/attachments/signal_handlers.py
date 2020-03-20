from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from .models import AttachmentRevision, TrashedAttachment


@receiver(
    post_delete, sender=AttachmentRevision, dispatch_uid="attachments.revision.delete"
)
def after_revision_delete(instance, **kwargs):
    """
    Signal handler to be called when an attachment revision is deleted
    """
    # see if there is a previous revision
    previous = instance.get_previous()
    # if yes, make it the current revision of the attachment
    if previous is not None:
        previous.make_current()


@receiver(pre_delete, sender=TrashedAttachment, dispatch_uid="attachments.trash.delete")
def on_trash_delete(instance, **kwargs):
    """
    Signal handler to be called when a trash item is deleted.
    """
    # if a file entry is present, delete the file with the storage
    # without saving the model instance
    if instance.file:
        instance.file.delete(save=False)
