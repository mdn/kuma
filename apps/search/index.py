import logging

from django.conf import settings

from elasticutils.contrib.django import get_es, S
from pyelasticsearch.exceptions import (ElasticHttpNotFoundError,
                                        IndexAlreadyExistsError)

from .decorators import _mapping_types
from .models import Index

log = logging.getLogger('mdn.search')


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
    return Index.objects.get_current().prefixed_name


def get_indexing_es(**kwargs):
    """Return ES instance with 30s timeout for indexing.

    :arg kwargs: any settings to override.

    :returns: an ES

    """
    defaults = {'timeout': settings.ES_INDEXING_TIMEOUT}
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


def recreate_index(es=None, index=None):
    """Delete index if it's there and creates a new one.

    :arg es: ES to use. By default, this creates a new indexing ES.

    """
    if es is None:
        es = get_indexing_es()

    mappings = {}
    analysis = None
    for name, mt in get_mapping_types().items():
        mapping = mt.get_mapping()
        if mapping is not None:
            mappings[name] = {'properties': mapping}

        analysis = mt.get_analysis()

    if index is None:
        index = get_index()

    delete_index_if_exists(index)

    # There should be no mapping-conflict race here since the index
    # doesn't exist. Live indexing should just fail.

    # Simultaneously create the index and the mappings, so live
    # indexing doesn't get a chance to index anything between the two
    # causing ES to infer a possibly bogus mapping (which causes ES to
    # freak out if the inferred mapping is incompatible with the
    # explicit mapping).
    settings = {
        'mappings': mappings,
        'settings': {
            'index': {
                'analysis': analysis
            }
        }
    }
    try:
        es.create_index(index, settings=settings)
    except IndexAlreadyExistsError:
        pass


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


def index_chunk(cls, chunk, reraise=False, es=None, index=None):
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

    cls.bulk_index(documents, id_field='id', es=es, index=index)
