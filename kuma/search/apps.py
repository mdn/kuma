from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from elasticsearch_dsl.connections import connections as es_connections


class SearchConfig(AppConfig):
    """Initialize the kuma.search application."""

    name = "kuma.search"
    verbose_name = _("Search")

    def ready(self):
        """Configure kuma.search after models are loaded."""
        # Configure Elasticsearch connections for connection pooling.
        es_connections.configure(
            default={"hosts": settings.ES_URLS},
            indexing={
                "hosts": settings.ES_URLS,
                "timeout": settings.ES_INDEXING_TIMEOUT,
            },
        )
