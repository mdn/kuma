from django.apps import AppConfig
from django.conf import settings
from elasticsearch_dsl.connections import connections


class APIConfig(AppConfig):
    """
    The Django App Config class to store information about the API app
    and do startup time things.
    """

    name = "kuma.api"
    verbose_name = "API"

    def ready(self):
        # Configure Elasticsearch connections for connection pooling.
        connections.configure(
            default={"hosts": settings.ES_URLS},
        )
