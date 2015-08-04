from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import signals
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from elasticsearch_dsl.connections import connections as es_connections

from .jobs import (DocumentContributorsJob, DocumentZoneStackJob,
                   DocumentZoneURLRemapsJob)
from .signals import render_done


def invalidate_zone_stack_cache(document, async=False):
    """
    Reset the cache for the zone stack for all of the documents
    in the document tree branch.
    """
    pks = [document.pk] + [parent.pk for parent in
                           document.get_topic_parents()]
    job = DocumentZoneStackJob()
    if async:
        invalidator = job.invalidate
    else:
        invalidator = job.refresh
    for pk in pks:
        invalidator(pk)


def invalidate_zone_urls_cache(document, async=False):
    """
    Reset the URL remap list cache for the given document, assuming it
    even has a zone.
    """
    job = DocumentZoneURLRemapsJob()
    if async:
        invalidator = job.invalidate
    else:
        invalidator = job.refresh
    try:
        if document.zone:
            # reset the cached list of zones of the document's locale
            invalidator(document.locale)
    except ObjectDoesNotExist:
        pass


def invalidate_zone_caches_for_document(sender, instance, **kwargs):
    """
    A signal handler to trigger the cache invalidation of both the zone URLs
    and stack cache for a given document.
    """
    async = kwargs.get('async', True)
    invalidate_zone_urls_cache(instance, async=async)
    invalidate_zone_stack_cache(instance, async=async)


def invalidate_zone_caches_for_zone(sender, instance, **kwargs):
    """
    A signal handler to trigger the cache invalidation of both the zone URLs
    and stack cache for a given zone's document.
    """
    invalidate_zone_caches_for_document(sender=instance.document.__class__,
                                        instance=instance.document,
                                        async=False)


def invalidate_contributors(sender, instance, **kwargs):
    """
    A signal handler to trigger the contributor bar for a given document.
    """
    DocumentContributorsJob().invalidate(instance.pk)


def build_json_data(sender, instance, **kwargs):
    """
    A signal handler to update the given document's json field.
    """
    from .tasks import build_json_data_for_document
    if not instance.deleted:
        build_json_data_for_document.delay(instance.pk, stale=False)


class WikiConfig(AppConfig):
    """
    The Django App Config class to store information about the wiki app
    and do startup time things.
    """
    name = 'kuma.wiki'
    verbose_name = _("Wiki")

    def ready(self):
        super(WikiConfig, self).ready()

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

        # the list of wiki document signal handlers to connect to
        Document = self.get_model('Document')
        signals.post_save.connect(invalidate_zone_caches_for_document,
                                  sender=Document,
                                  dispatch_uid='wiki.zones.invalidate.document')
        signals.post_save.connect(invalidate_contributors,
                                  sender=Document,
                                  dispatch_uid='wiki.contributors.invalidate')
        render_done.connect(build_json_data,
                            dispatch_uid='wiki.document.build_json')

        # the list of wiki document zone signal handlers to connect to
        DocumentZone = self.get_model('DocumentZone')
        signals.post_save.connect(invalidate_zone_caches_for_zone,
                                  sender=DocumentZone,
                                  dispatch_uid='wiki.zones.invalidate.zone')
