from django.apps import AppConfig
from django.conf import settings
from django.core.checks import register
from django.utils.translation import gettext_lazy as _


class UserNewsletterConfig(AppConfig):
    """
    The Django App Config class to store information about the users app
    and do startup time things.
    """

    name = "kuma.users.newsletter"
    verbose_name = _("UserNewsletter")

    def ready(self):
        if not settings.SENDINBLUE_API_KEY:
            return

        # Connect signal handlers
        from . import signal_handlers  # noqa

        from .checks import sendinblue_check

        register(sendinblue_check)
