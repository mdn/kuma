from django.apps import AppConfig

from kuma.celery import app


class DocumentURLsConfig(AppConfig):
    name = "kuma.documenturls"
    verbose_name = "Document URLs"

    def ready(self):
        from kuma.documenturls.tasks import refresh_document_urls

        app.add_periodic_task(60, refresh_document_urls.s())
