from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from elasticsearch_dsl.connections import connections as es_connections


class WikiConfig(AppConfig):
    """
    The Django App Config class to store information about the wiki app
    and do startup time things.
    """
    name = 'kuma.wiki'
    verbose_name = _("Wiki")

    def ready(self):
        '''Configure kuma.wiki after models are loaded.'''
        # Register signal handlers
        from . import signal_handlers  # noqa

        # Configure Elasticsearch connections for connection pooling.
        es_connections.configure(
            default={
                'hosts': settings.ES_URLS,
            },
            indexing={
                'hosts': settings.ES_URLS,
                'timeout': settings.ES_INDEXING_TIMEOUT,
            },
        )
