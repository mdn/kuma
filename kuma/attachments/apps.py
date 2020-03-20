from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AttachmentsConfig(AppConfig):
    """
    The Django App Config class to store information about the users app
    and do startup time things.
    """

    name = "kuma.attachments"
    verbose_name = _("Attachments")

    def ready(self):
        # Register signal handlers
        from . import signal_handlers  # noqa
