import logging
import warnings

from django.conf import settings
from django.db.models.signals import pre_delete

# ignore a deprecation warning from elasticutils until the fix is released
# refs https://github.com/mozilla/elasticutils/pull/160
warnings.filterwarnings("ignore",
                        category=DeprecationWarning,
                        module='celery.decorators')

from elasticutils.contrib.django.tasks import index_objects, unindex_objects

from wiki.signals import render_done


def render_done_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return
    instance = kwargs['instance']
    mappping_type = instance.get_mapping_type()
    if mappping_type.should_update(instance):
        try:
            index_objects.delay(mappping_type, [instance.id])
        except:
            logging.error('Search indexing task failed',
                          exc_info=True)
    else:
        logging.info('Ignoring wiki document %r while updating search index',
                     instance.id, exc_info=True)


def pre_delete_handler(**kwargs):
    if not settings.ES_LIVE_INDEX or 'instance' not in kwargs:
        return
    instance = kwargs['instance']
    mappping_type = instance.get_mapping_type()
    if mappping_type.should_update(instance):
        unindex_objects.delay(mappping_type, [instance.id])
    else:
        logging.info('Ignoring wiki document %r while updating search index',
                     instance.id, exc_info=True)


def register_live_index(model_cls):
    """Register a model and index for auto indexing."""
    uid = str(model_cls) + 'live_indexing'
    render_done.connect(render_done_handler, model_cls, dispatch_uid=uid)
    pre_delete.connect(pre_delete_handler, model_cls, dispatch_uid=uid)
    # Enable this to be used as decorator.
    return model_cls
