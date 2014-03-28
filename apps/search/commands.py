import logging
import time

from django.conf import settings
from django.db import reset_queries
from pyelasticsearch.exceptions import ElasticHttpNotFoundError

from .decorators import requires_good_connection
from .index import (get_indexing_es, get_index, recreate_index, get_indexable,
                    index_chunk, get_indexes, delete_index_if_exists,
                    get_index_stats)
from .utils import chunked, format_time

log = logging.getLogger('mdn.search')


@requires_good_connection
def es_reindex_cmd(percent=100, mapping_types=None,
                   chunk_size=1000, index=None):
    """Rebuild ElasticSearch indexes.

    :arg percent: 1 to 100--the percentage of the db to index
    :arg mapping_types: list of mapping types to index

    """
    es = get_indexing_es()

    if index is None:
        index = get_index()

    log.info('Wiping and recreating %s....', index)
    recreate_index(es=es, index=index)

    if mapping_types:
        indexable = get_indexable(percent, mapping_types)
    else:
        indexable = get_indexable(percent)

    # We're doing a lot of indexing, so we get the refresh_interval
    # currently in the index, then nix refreshing. Later we'll restore it.
    index_settings = (es.get_settings(index)
                        .get(index, {}).get('settings', {}))
    refresh_interval = index_settings.get('index.refresh_interval', '1s')
    number_of_replicas = index_settings.get('number_of_replicas', '1')

    # Disable automatic refreshing
    temporary_settings = {
        'index': {
            'refresh_interval': '-1',
            'number_of_replicas': '0',
        }
    }

    try:
        es.update_settings(index, temporary_settings)
        start_time = time.time()

        for cls, indexable in indexable:
            cls_start_time = time.time()
            total = len(indexable)

            if total == 0:
                continue

            log.info('Reindex %s. %s to index....',
                     cls.get_mapping_type_name(), total)

            i = 0
            for chunk in chunked(indexable, chunk_size):
                index_chunk(cls, chunk, es=es, index=index)

                i += len(chunk)
                time_to_go = (total - i) * ((time.time() - start_time) / i)
                per_chunk_size = (time.time() - start_time) / (i / float(chunk_size))
                log.info('%s/%s... (%s to go, %s per %s docs)', i, total,
                         format_time(time_to_go),
                         format_time(per_chunk_size),
                         chunk_size)

                # We call this every 1000 or so because we're
                # essentially loading the whole db and if DEBUG=True,
                # then Django saves every sql statement which causes
                # our memory to go up up up. So we reset it and that
                # makes things happier even in DEBUG environments.
                reset_queries()

            delta_time = time.time() - cls_start_time
            log.info('Done! (%s, %s per %s docs)',
                     format_time(delta_time),
                     format_time(delta_time / (total / float(per_chunk_size))),
                     chunk_size)

    finally:
        # Re-enable automatic refreshing
        reset_settings = {
            'index': {
                'refresh_interval': refresh_interval,
                'number_of_replicas': number_of_replicas,
            }
        }
        es.update_settings(index, reset_settings)
        delta_time = time.time() - start_time
        log.info('Done! (total time: %s)', format_time(delta_time))


@requires_good_connection
def es_delete_cmd(index=None):
    """Delete a specified index."""
    indexes = [name for name, count in get_indexes()]

    if index is None:
        index = get_index()

    if index not in indexes:
        log.error('Index "%s" is not a valid index.', index)
        if not indexes:
            log.error('There are no valid indexes.')
        else:
            log.error('Valid indexes: %s', ', '.join(indexes))
        return

    ret = raw_input('Are you sure you want to delete "%s"? (yes/no) ' % index)
    if ret != 'yes':
        return

    log.info('Deleting index "%s"...', index)
    delete_index_if_exists(index)
    log.info('Done!')


@requires_good_connection
def es_status_cmd(index=None):
    """Show ElasticSearch index status."""
    log.info('Settings:')
    log.info('  ES_URLS               : %s', settings.ES_URLS)
    log.info('  ES_INDEX_PREFIX       : %s', settings.ES_INDEX_PREFIX)
    log.info('  ES_INDEXES            : %s', settings.ES_INDEXES)

    if index is None:
        index = get_index()

    log.info('Index (%s) stats:', index)

    try:
        mt_stats = get_index_stats()
        log.info('  Index (%s):', index)
        for name, count in mt_stats.items():
            log.info('    %-20s: %d', name, count)

    except ElasticHttpNotFoundError:
        log.info('  Index does not exist. (%s)', index)
