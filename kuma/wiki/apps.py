from celery.schedules import crontab
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from kuma.celery import app


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

        # Build sitemaps every day at 05:00
        from kuma.wiki.tasks import build_sitemaps

        app.add_periodic_task(
            crontab(minute=0, hour=5), build_sitemaps.s(),
        )

        # Render stale documents: every 60 minutes
        from kuma.wiki.tasks import render_stale_documents

        app.add_periodic_task(60 * 60, render_stale_documents.s())
