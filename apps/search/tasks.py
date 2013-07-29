from django.conf import settings
from django.db.models.signals import pre_delete

from celery.task import task

from wiki.signals import render_done


@task
def index_item_task(mapping_type, item_id, **kwargs):
    doc = mapping_type.extract_document(item_id)
    mapping_type.index(doc, item_id)


@task
def unindex_item_task(mapping_type, item_id, **kwargs):
    mapping_type.unindex(item_id)


def render_done_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return
    instance = kwargs['instance']
    index_item_task.delay(instance.get_mapping_type(), instance.id)


def pre_delete_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return
    instance = kwargs['instance']
    unindex_item_task.delay(instance.get_mapping_type(), instance.id)


def register_live_index(model_cls):
    """Register a model and index for auto indexing."""
    uid = str(model_cls) + 'live_indexing'
    render_done.connect(render_done_handler, model_cls, dispatch_uid=uid)
    pre_delete.connect(pre_delete_handler, model_cls, dispatch_uid=uid)
    # Enable this to be used as decorator.
    return model_cls
