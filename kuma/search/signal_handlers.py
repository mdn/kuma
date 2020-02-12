import logging

from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from kuma.wiki.models import Document
from kuma.wiki.search import WikiDocumentType
from kuma.wiki.signals import render_done
from kuma.wiki.tasks import index_documents, unindex_documents

from .models import Index

log = logging.getLogger("kuma.search.signals")


@receiver(render_done, sender=Document, dispatch_uid="search.render_done.live_indexing")
def render_done_handler(instance, **kwargs):
    if not settings.ES_LIVE_INDEX:
        return

    doc = instance
    if WikiDocumentType.should_update(doc):
        current_index = Index.objects.get_current()
        outdated = current_index.record_outdated(doc)
        if outdated:
            log.info(
                "Found a newer index and scheduled " "indexing it after promotion."
            )
        doc_pks = {item.pk for item in doc.other_translations}
        doc_pks.add(doc.id)
        try:
            index_documents.delay(list(doc_pks), current_index.pk)
        except Exception:
            log.error("Search indexing task failed", exc_info=True)
    else:
        log.info(
            "Ignoring wiki document %r while updating search index",
            doc.id,
            exc_info=True,
        )


@receiver(pre_delete, sender=Document, dispatch_uid="seach.pre_delete.live_indexing")
def pre_delete_handler(instance, **kwargs):
    if not settings.ES_LIVE_INDEX:
        return

    doc = instance
    current_index = Index.objects.get_current()

    if WikiDocumentType.should_update(doc):
        unindex_documents.delay([doc.pk], current_index.pk)
    else:
        log.info(
            "Ignoring wiki document %r while updating search index",
            doc.pk,
            exc_info=True,
        )
