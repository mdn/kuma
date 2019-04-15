from django.apps import AppConfig


class APIConfig(AppConfig):
    """
    The Django App Config class to store information about the API app
    and do startup time things.
    """
    name = 'kuma.api'
    verbose_name = 'API'

    def ready(self):
        """Configure kuma.api after models are loaded."""
        # Register signal handlers
        from . import signal_handlers  # noqa
