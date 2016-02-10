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

    def on_trash_delete(self, **kwargs):
        """
        Signal handler to be called when a trash item is deleted.
        """
        instance = kwargs.get('instance', None)
        if instance is not None:
            if instance.file:
                instance.file.delete(save=False)
