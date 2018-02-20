from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SearchConfig(AppConfig):
    """Initialize the kuma.search application."""
    name = 'kuma.search'
    verbose_name = _('Search')

    def ready(self):
        # Register signal handlers
        from . import signal_handlers  # noqa
