import logging

from django.conf import settings

from kuma.wiki.search import WikiDocumentType


log = logging.getLogger('kuma.search.signals')


def render_done_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return

    from kuma.wiki.tasks import index_documents
    from .models import Index

    doc = kwargs['instance']
    if WikiDocumentType.should_update(doc):
        current_index = Index.objects.get_current()
        outdated = current_index.record_outdated(doc)
        if outdated:
            log.info('Found a newer index and scheduled '
                     'indexing it after promotion.')
        doc_pks = set(doc.other_translations.values_list('pk', flat=True))
        doc_pks.add(doc.id)
        try:
            index_documents.delay(list(doc_pks), current_index.pk)
        except:
            log.error('Search indexing task failed', exc_info=True)
    else:
        log.info('Ignoring wiki document %r while updating search index',
                 doc.id, exc_info=True)


def pre_delete_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return

    from kuma.wiki.tasks import unindex_documents
    from .models import Index

    doc = kwargs['instance']
    current_index = Index.objects.get_current()

    if WikiDocumentType.should_update(doc):
        unindex_documents.delay([doc.pk], current_index.pk)
    else:
        log.info('Ignoring wiki document %r while updating search index',
                 doc.pk, exc_info=True)
