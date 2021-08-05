from django.apps import AppConfig
from django.conf import settings

from kuma.celery import app


class DocumentURLsConfig(AppConfig):
    name = "kuma.documenturls"
    verbose_name = "Document URLs"

    def ready(self):
        from kuma.documenturls.tasks import refresh_documenturls

        app.add_periodic_task(
            settings.REFRESH_DOCUMENTURLS_PERIODICITY_SECONDS, refresh_documenturls.s()
        )
