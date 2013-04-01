from django.conf import settings
from django.db.models.signals import post_save, pre_delete

from celery.task import task


@task
def index_item_task(mapping_type, item_id, **kwargs):
    doc = mapping_type.extract_document(item_id)
    mapping_type.index(doc, item_id)


@task
def unindex_item_task(mapping_type, item_id, **kwargs):
    mapping_type.unindex(item_id)


def _live_index_handler(sender, **kwargs):
    if (not settings.ES_LIVE_INDEX or
        'signal' not in kwargs or 'instance' not in kwargs):
        return

    instance = kwargs['instance']

    if kwargs['signal'] == post_save:
        index_item_task.delay(instance.get_mapping_type(), instance.id)

    if kwargs['signal'] == pre_delete:
        unindex_item_task.delay(instance.get_mapping_type(), instance.id)


def register_live_index(model_cls):
    """Register a model and index for auto indexing."""
    uid = str(model_cls) + 'live_indexing'
    post_save.connect(_live_index_handler, model_cls, dispatch_uid=uid)
    pre_delete.connect(_live_index_handler, model_cls, dispatch_uid=uid)
    # Enable this to be used as decorator.
    return model_cls
