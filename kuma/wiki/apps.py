from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WikiConfig(AppConfig):
    """
    The Django App Config class to store information about the wiki app
    and do startup time things.
    """

    name = "kuma.wiki"
    verbose_name = _("Wiki")

    def ready(self):
        """Configure kuma.wiki after models are loaded."""
        # Register signal handlers
        from . import signal_handlers  # noqa
