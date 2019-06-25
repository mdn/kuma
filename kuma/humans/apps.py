from __future__ import unicode_literals

from celery.schedules import crontab
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from kuma.celery import app


class HumansConfig(AppConfig):
    """
    The Django App Config class to store information about the humans app
    and do startup time things.
    """
    name = 'kuma.humans'
    verbose_name = _('Humans')

    def ready(self):
        """Configure kuma.humans after models are loaded."""

        # Refresh humans.txt every day at 00:00
        from kuma.humans.tasks import humans_txt
        app.add_periodic_task(
            crontab(minute=0, hour=0),
            humans_txt.s()
        )
