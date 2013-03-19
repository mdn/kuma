import logging
import time
from itertools import islice

from django.conf import settings
from django.db import reset_queries

from elasticutils.contrib.django import get_es, S
from elasticutils.contrib.django.models import DjangoMappingType
from pyelasticsearch.exceptions import (ConnectionError, Timeout,
                                        ElasticHttpNotFoundError)


# Note: This module should not import any Fjord modules. Otherwise we
# get into import recursion issues.


log = logging.getLogger('i.search')


_mapping_types = {}


def register_mapping_type(mapping_type):
    """Registers a mapping type.

    This gives us a way to get all the registered mapping types for
    indexing.

    """
    _mapping_types[mapping_type.get_mapping_type_name()] = mapping_type
    # Enable this to be used as a decorator
    return mapping_type


def get_mapping_types(mapping_types=None):
    """Returns a dict of name -> mapping type.

    :arg mapping_types: list of mapping type names to restrict
        the dict to.

    """
    if mapping_types is None:
        return _mapping_types

    return dict((key, val) for key, val in _mapping_types.items()
                if key in mapping_types)


def get_index():
    """Returns the index we're using."""

    # Note: This could probably be defined in utils, but it's defined
    # here because otherwise models imports utils and utils imports
    # models and that turns into a mess.
    return '%s-%s' % (settings.ES_INDEX_PREFIX, settings.ES_INDEXES['default'])


class SearchMappingType(DjangoMappingType):
    """DjangoMappingType with correct index."""
    @classmethod
    def get_index(cls):
        return get_index()


def format_time(time_to_go):
    """Return minutes and seconds string for given time in seconds.

    :arg time_to_go: Number of seconds to go.

    :returns: string representation of how much time to go.
    """
    if time_to_go < 60:
        return '%ds' % time_to_go
    return '%dm %ds' % (time_to_go / 60, time_to_go % 60)


def create_batch_id():
    """Returns a batch_id"""
    # TODO: This is silly, but it's a good enough way to distinguish
    # between batches by looking at a Record. This is just over the
    # number of seconds in a day.
    return str(int(time.time()))[-6:]


def chunked(iterable, n):
    """Return chunks of n length of iterable.

    If ``len(iterable) % n != 0``, then the last chunk will have
    length less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :arg iterable: the iterable
    :arg n: the chunk length

    :returns: generator of chunks from the iterable
    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def get_indexing_es(**kwargs):
    """Return ES instance with 30s timeout for indexing.

    :arg kwargs: any settings to override.

    :returns: an ES

    """
    defaults = {
        'timeout': settings.ES_INDEXING_TIMEOUT
        }
    defaults.update(kwargs)

    return get_es(**defaults)


def get_indexes(all_indexes=False):
    """Return list of (name, count) tuples for indexes.

    :arg all_indexes: True if you want to see all indexes and
        False if you want to see only indexes prefexed with
        ``settings.ES_INDEX_PREFIX``.

    :returns: list of (name, count) tuples.

    """
    es = get_indexing_es()

    status = es.status()
    indexes = status['indices']

    if not all_indexes:
        indexes = dict((k, v) for k, v in indexes.items()
                       if k.startswith(settings.ES_INDEX_PREFIX))

    indexes = [(k, v['docs']['num_docs']) for k, v in indexes.items()]

    return indexes


def delete_index_if_exists(index):
    """Delete the specified index.

    :arg index: The name of the index to delete.

    """
    try:
        get_indexing_es().delete_index(index)
    except ElasticHttpNotFoundError:
        # Can ignore this since it indicates the index doesn't exist
        # and therefore there's nothing to delete.
        pass


def get_index_stats():
    """Return dict of name -> count for documents indexed.

    For example:

    >>> get_index_stats()
    {'simple': 122233}

    .. Note::

       This infers the index to use from the registered mapping
       types.

    :returns: mapping type name -> count for documents indexes.

    :throws pyelasticsearch.exceptions.Timeout: if the request
        times out
    :throws pyelasticsearch.exceptions.ConnectionError: if there's a
        connection error
    :throws pyelasticsearch.exceptions.ElasticHttpNotFound: if the
        index doesn't exist

    """
    stats = {}
    for name, cls in get_mapping_types().items():
        stats[name] = S(cls).count()

    return stats


def recreate_index(es=None):
    """Delete index if it's there and creates a new one.

    :arg es: ES to use. By default, this creates a new indexing ES.

    """
    if es is None:
        es = get_indexing_es()

    mappings = {}
    for name, mt in get_mapping_types().items():
        mapping = mt.get_mapping()
        if mapping is not None:
            mappings[name] = {'properties': mapping}

    index = get_index()

    delete_index_if_exists(index)

    # There should be no mapping-conflict race here since the index
    # doesn't exist. Live indexing should just fail.

    # Simultaneously create the index and the mappings, so live
    # indexing doesn't get a chance to index anything between the two
    # causing ES to infer a possibly bogus mapping (which causes ES to
    # freak out if the inferred mapping is incompatible with the
    # explicit mapping).

    es.create_index(index, settings={'mappings': mappings})


def get_indexable(percent=100, mapping_types=None):
    """Return list of (class, iterable) for all the things to index.

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.
    :arg mapping_types: List of mapping types to index. Defaults to
        indexing all mapping types.

    :returns: list of (mapping type class, iterable) for all mapping
        types

    """
    to_index = []
    percent = float(percent) / 100

    for name, cls in get_mapping_types(mapping_types).items():
        indexable = cls.get_indexable()
        if percent < 1:
            indexable = indexable[:int(indexable.count() * percent)]
        to_index.append((cls, indexable))

    return to_index


def index_chunk(cls, chunk, reraise=False, es=None):
    """Index a chunk of documents.

    :arg cls: The MappingType class.
    :arg chunk: Iterable of ids of that MappingType to index.
    :arg reraise: False if you want errors to be swallowed and True
        if you want errors to be thrown.
    :arg es: The ES to use. Defaults to creating a new indexing ES.

    .. Note::

       This indexes all the documents in the chunk in one single bulk
       indexing call. Keep that in mind when you break your indexing
       task into chunks.

    """
    if es is None:
        es = get_indexing_es()

    documents = []
    for id_ in chunk:
        try:
            documents.append(cls.extract_document(id_))
        except Exception:
            log.exception('Unable to extract/index document (id: %d)', id_)
            if reraise:
                raise

    cls.bulk_index(documents, id_field='id', es=es)


def requires_good_connection(fun):
    """Decorator that logs an error on connection issues

    9 out of 10 doctors say that connection errors are usually because
    ES_URLS is set wrong. This catches those errors and helps you out
    with fixing it.

    """
    def _requires_good_connection(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except (ConnectionError, Timeout):
            log.error('Either your ElasticSearch process is not quite '
                      'ready to rumble, is not running at all, or ES_URLS'
                      'is set wrong in your settings_local.py file.')
    return _requires_good_connection


@requires_good_connection
def es_reindex_cmd(percent=100, mapping_types=None):
    """Rebuild ElasticSearch indexes.

    :arg percent: 1 to 100--the percentage of the db to index
    :arg mapping_types: list of mapping types to index

    """
    es = get_indexing_es()

    log.info('Wiping and recreating %s....', get_index())
    recreate_index(es=es)

    if mapping_types:
        indexable = get_indexable(percent, mapping_types)
    else:
        indexable = get_indexable(percent)

    start_time = time.time()

    for cls, indexable in indexable:
        cls_start_time = time.time()
        total = len(indexable)

        if total == 0:
            continue

        log.info('Reindex %s. %s to index....',
                 cls.get_mapping_type_name(), total)

        i = 0
        for chunk in chunked(indexable, 1000):
            index_chunk(cls, chunk, es=es)

            i += len(chunk)
            time_to_go = (total - i) * ((time.time() - start_time) / i)
            per_1000 = (time.time() - start_time) / (i / 1000.0)
            log.info('%s/%s... (%s to go, %s per 1000 docs)', i, total,
                     format_time(time_to_go),
                     format_time(per_1000))

            # We call this every 1000 or so because we're
            # essentially loading the whole db and if DEBUG=True,
            # then Django saves every sql statement which causes
            # our memory to go up up up. So we reset it and that
            # makes things happier even in DEBUG environments.
            reset_queries()

        delta_time = time.time() - cls_start_time
        log.info('Done! (%s, %s per 1000 docs)',
                 format_time(delta_time),
                 format_time(delta_time / (total / 1000.0)))

    delta_time = time.time() - start_time
    log.info('Done! (total time: %s)', format_time(delta_time))


@requires_good_connection
def es_delete_cmd(index):
    """Delete a specified index."""
    indexes = [name for name, count in get_indexes()]

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
def es_status_cmd(checkindex=False):
    """Show ElasticSearch index status."""
    log.info('Settings:')
    log.info('  ES_URLS               : %s', settings.ES_URLS)
    log.info('  ES_INDEX_PREFIX       : %s', settings.ES_INDEX_PREFIX)
    log.info('  ES_INDEXES            : %s', settings.ES_INDEXES)

    log.info('Index (%s) stats:', get_index())

    try:
        mt_stats = get_index_stats()
        log.info('  Index (%s):', get_index())
        for name, count in mt_stats.items():
            log.info('    %-20s: %d', name, count)

    except ElasticHttpNotFoundError:
        log.info('  Index does not exist. (%s)', get_index())
