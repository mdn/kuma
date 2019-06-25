from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from kuma.celery import app


class FeederConfig(AppConfig):
    """
    The Django App Config class to store information about the feeder app
    and do startup time things.
    """
    name = 'kuma.feeder'
    verbose_name = _('Feeder')

    def ready(self):
        """Configure kuma.feeder after models are loaded."""

        # Refresh Hacks Blog: every 10 minutes
        from kuma.feeder.tasks import update_feeds
        app.add_periodic_task(
            60 * 10,
            update_feeds.s()
        )
