# -*- coding: utf-8 -*-
from __future__ import division

import logging
import operator
import time

from django.conf import settings
from django.db.models import Q
from django.utils.html import strip_tags
from django.db import reset_queries

from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import document, field
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.mapping import Mapping
from elasticsearch_dsl.search import Search

from kuma.core.utils import chunked
from kuma.search.utils import format_time


log = logging.getLogger('kuma.wiki.search')


# Configure Elasticsearch connections for connection pooling.
connections.configure(
    default={'hosts': settings.ES_URLS},
    indexing={'hosts': settings.ES_URLS,
              'timeout': settings.ES_INDEXING_TIMEOUT},
)


class WikiDocumentType(document.DocType):
    excerpt_fields = ['summary', 'content']
    exclude_slugs = ['Talk:', 'User:', 'User_talk:', 'Template_talk:',
                     'Project_talk:']

    boost = field.Float(null_value=1.0)
    content = field.String(analyzer='kuma_content',
                           term_vector='with_positions_offsets')
    css_classnames = field.String(analyzer='case_insensitive_keyword')
    html_attributes = field.String(analyzer='case_insensitive_keyword')
    id = field.Long()
    kumascript_macros = field.String(analyzer='case_insensitive_keyword')
    locale = field.String(index='not_analyzed')
    modified = field.Date()
    parent = field.Nested(properties={
        'id': field.Long(),
        'title': field.String(analyzer='kuma_title'),
        'slug': field.String(index='not_analyzed'),
        'locale': field.String(index='not_analyzed'),
    })
    slug = field.String(index='not_analyzed')
    summary = field.String(analyzer='kuma_content',
                           term_vector='with_positions_offsets')
    tags = field.String(analyzer='case_sensitive')
    title = field.String(analyzer='kuma_title', boost=1.2)

    class Meta(object):
        mapping = Mapping('wiki_document')
        mapping.meta('_all', enalbed=False)

    @classmethod
    def get_connection(cls, alias='default'):
        return connections.get_connection(alias)

    @classmethod
    def get_doc_type(cls):
        return cls._doc_type.name

    @classmethod
    def from_django(cls, obj):
        doc = {
            'id': obj.id,
            'title': obj.title,
            'slug': obj.slug,
            'summary': obj.get_summary(strip_markup=True),
            'locale': obj.locale,
            'modified': obj.modified,
            'content': strip_tags(obj.rendered_html),
            'tags': list(obj.tags.values_list('name', flat=True)),
            'kumascript_macros': obj.extract_kumascript_macro_names(),
            'css_classnames': obj.extract_css_classnames(),
            'html_attributes': obj.extract_html_attributes(),
        }
        if obj.zones.exists():
            # boost all documents that are a zone
            doc['boost'] = 8.0
        elif obj.slug.count('/') == 1:
            # a little boost if no zone but still first level
            doc['boost'] = 4.0
        else:
            doc['boost'] = 1.0
        if obj.parent:
            doc['parent'] = {
                'id': obj.parent.id,
                'title': obj.parent.title,
                'locale': obj.parent.locale,
                'slug': obj.parent.slug,
            }
        else:
            doc['parent'] = {}

        return doc

    @classmethod
    def get_mapping(cls):
        return cls._doc_type.mapping.to_dict()

    @classmethod
    def get_analysis(cls):
        return {
            'filter': {
                'kuma_word_delimiter': {
                    'type': 'word_delimiter',
                    'preserve_original': True,  # hi-fi -> hifi, hi-fi
                    'catenate_words': True,  # hi-fi -> hifi
                    'catenate_numbers': True,  # 90-210 -> 90210
                }
            },
            'analyzer': {
                'default': {
                    'tokenizer': 'standard',
                    'filter': ['standard', 'elision']
                },
                # a custom analyzer that strips html and uses our own
                # word delimiter filter and the elision filter
                # (e.g. L'attribut -> attribut). The rest is the same as
                # the snowball analyzer
                'kuma_content': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'char_filter': ['html_strip'],
                    'filter': [
                        'elision',
                        'kuma_word_delimiter',
                        'lowercase',
                        'standard',
                        'stop',
                        'snowball',
                    ],
                },
                'kuma_title': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'elision',
                        'kuma_word_delimiter',
                        'lowercase',
                        'standard',
                        'snowball',
                    ],
                },
                'case_sensitive': {
                    'type': 'custom',
                    'tokenizer': 'keyword'
                },
                'case_insensitive_keyword': {
                    'type': 'custom',
                    'tokenizer': 'keyword',
                    'filter': 'lowercase'
                }
            },
        }

    @classmethod
    def get_settings(cls):
        return {
            'mappings': cls.get_mapping(),
            'settings': {
                'analysis': cls.get_analysis(),
                'number_of_replicas': settings.ES_DEFAULT_NUM_REPLICAS,
                'number_of_shards': settings.ES_DEFAULT_NUM_SHARDS,
            }
        }

    @classmethod
    def bulk_index(cls, documents, id_field='id', es=None, index=None):
        """Index of a bunch of documents."""
        es = es or cls.get_connection()
        index = index or cls.get_index()
        type = cls.get_doc_type()

        actions = [
            {'_index': index, '_type': type, '_id': d['id'], '_source': d}
            for d in documents]

        bulk(es, actions)

    @classmethod
    def bulk_delete(cls, ids, es=None, index=None):
        """Index of a bunch of documents."""
        es = es or cls.get_connection()
        index = index or cls.get_index()
        type = cls.get_doc_type()

        actions = [
            {'_op_type': 'delete', '_index': index, '_type': type, '_id': _id}
            for _id in ids]

        bulk(es, actions)

    @classmethod
    def get_index(cls):
        from kuma.search.models import Index
        return Index.objects.get_current().prefixed_name

    @classmethod
    def search(cls, **kwargs):
        kwargs.update({
            'using': connections.get_connection(),
            'index': cls.get_index(),
            'doc_type': {cls._doc_type.name: cls.from_es},
        })
        sq = Search(**kwargs)

        # Add highlighting.
        sq = sq.highlight(*cls.excerpt_fields)
        sq = sq.highlight_options(order='score')

        return sq

    @classmethod
    def get_model(cls):
        from kuma.wiki.models import Document
        return Document

    @classmethod
    def get_indexable(cls, percent=100):
        """
        For this mapping type return a list of model IDs that should be
        indexed with the management command, in a full reindex.

        WARNING: When changing this code make sure to update the
                 ``should_update`` method below, too!

        """
        model = cls.get_model()

        excludes = []
        for exclude in cls.exclude_slugs:
            excludes.append(Q(slug__icontains=exclude))

        qs = (model.objects
                   .filter(is_template=False,
                           is_redirect=False,
                           deleted=False)
                   .exclude(reduce(operator.or_, excludes)))

        percent = percent / 100
        if percent < 1:
            qs = qs[:int(qs.count() * percent)]

        return qs.values_list('id', flat=True)

    @classmethod
    def should_update(cls, obj):
        """
        Given a Document instance should return boolean value
        whether the instance should be indexed or not.

        WARNING: This *must* mirror the logic of the ``get_indexable``
                 method above!
        """
        return (not obj.is_template and
                not obj.is_redirect and
                not obj.deleted and
                not any([exclude in obj.slug
                         for exclude in cls.exclude_slugs]))

    def get_excerpt(self):
        if getattr(self, 'highlight', False):
            for excerpt_field in self.excerpt_fields:
                if excerpt_field in self.highlight:
                    return u'…'.join(self.highlight[excerpt_field])
        return self.summary

    @classmethod
    def reindex_all(cls, chunk_size=1000, index=None, percent=100):
        """Rebuild ElasticSearch indexes.

        :arg chunk_size: how many documents to bulk index as a single chunk.
        :arg index: the `Index` object to reindex into. Uses the current promoted
            index if none provided.
        :arg percent: 1 to 100--the percentage of the db to index.

        """
        from kuma.search.models import Index
        from kuma.wiki.tasks import index_documents

        index = index or Index.objects.get_current()
        index_name = index.prefixed_name

        es = cls.get_connection('indexing')

        log.info('Wiping and recreating %s....', index_name)
        Index.objects.recreate_index(es=es, index=index)

        indexable = WikiDocumentType.get_indexable(percent)

        # We're doing a lot of indexing, so we get the refresh_interval
        # currently in the index, then nix refreshing. Later we'll restore it.
        index_settings = {}
        try:
            index_settings = (es.indices.get_settings(index_name)
                                .get(index_name, {}).get('settings', {}))
        except NotFoundError:
            pass

        refresh_interval = index_settings.get(
            'index.refresh_interval', settings.ES_DEFAULT_REFRESH_INTERVAL)
        number_of_replicas = index_settings.get(
            'number_of_replicas', settings.ES_DEFAULT_NUM_REPLICAS)

        # Disable automatic refreshing.
        temporary_settings = {
            'index': {
                'refresh_interval': '-1',
                'number_of_replicas': '0',
            }
        }

        try:
            es.indices.put_settings(temporary_settings, index=index_name)
            start_time = time.time()

            cls_start_time = time.time()
            total = len(indexable)

            if total == 0:
                return

            log.info('Reindex %s. %s to index...', cls.get_doc_type(), total)

            i = 0
            for chunk in chunked(indexable, chunk_size):
                index_documents(chunk, index.pk)

                i += len(chunk)
                time_to_go = (total - i) * ((time.time() - start_time) / i)
                per_chunk_size = ((time.time() - start_time) /
                                  (i / float(chunk_size)))
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
            es.indices.put_settings(reset_settings, index_name)
            delta_time = time.time() - start_time
            log.info('Done! (total time: %s)', format_time(delta_time))
