import logging

from django.conf import settings
from elasticutils.contrib.django.tasks import index_objects, unindex_objects


log = logging.getLogger('kuma.search')


def render_done_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return
    from .models import Index
    doc = kwargs['instance']
    mappping_type = doc.get_mapping_type()
    if mappping_type.should_update(doc):
        current_index = Index.objects.get_current()
        outdated = current_index.record_outdated(doc)
        if outdated:
            log.info('Found a newer index and scheduled '
                     'indexing it after promotion.')
        doc_pks = set(doc.other_translations.values_list('pk', flat=True))
        doc_pks.add(doc.id)
        try:
            index_objects.delay(mappping_type, list(doc_pks))
        except:
            log.error('Search indexing task failed', exc_info=True)
    else:
        log.info('Ignoring wiki document %r while updating search index',
                 doc.id, exc_info=True)


def pre_delete_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return
    instance = kwargs['instance']
    mappping_type = instance.get_mapping_type()
    if mappping_type.should_update(instance):
        unindex_objects.delay(mappping_type, [instance.id])
    else:
        log.info('Ignoring wiki document %r while updating search index',
                 instance.id, exc_info=True)


def delete_index(**kwargs):
    instance = kwargs.get('instance', None)
    if instance is not None:
        from .index import delete_index_if_exists
        delete_index_if_exists(instance.prefixed_name)
