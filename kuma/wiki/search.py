# -*- coding: utf-8 -*-
from __future__ import division

import logging
import operator
from math import ceil

from celery import chain
from django.conf import settings
from django.db.models import Q
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from elasticsearch.helpers import bulk
from elasticsearch_dsl import document, field
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.mapping import Mapping
from elasticsearch_dsl.search import Search
from six.moves import reduce

from kuma.core.utils import chord_flow, chunked

from .constants import EXPERIMENT_TITLE_PREFIX


log = logging.getLogger('kuma.wiki.search')


class WikiDocumentType(document.Document):
    excerpt_fields = ['summary', 'content']
    exclude_slugs = ['Talk:', 'User:', 'User_talk:', 'Template_talk:',
                     'Project_talk:', EXPERIMENT_TITLE_PREFIX]

    boost = field.Float(null_value=1.0)
    content = field.Text(analyzer='kuma_content',
                         term_vector='with_positions_offsets')
    css_classnames = field.Keyword()
    html_attributes = field.Keyword()
    id = field.Long()
    kumascript_macros = field.Keyword()
    locale = field.Keyword()
    modified = field.Date()
    parent = field.Object(properties={
        'id': field.Long(),
        'title': field.Text(analyzer='kuma_title'),
        'slug': field.Keyword(),
        'locale': field.Keyword(),
    })
    slug = field.Keyword()
    summary = field.Text(analyzer='kuma_content',
                         term_vector='with_positions_offsets')
    tags = field.Keyword()
    title = field.Text(analyzer='kuma_title')

    class Meta(object):
        mapping = Mapping('wiki_document')
        mapping.meta('_all', enabled=False)

    @classmethod
    def get_connection(cls, alias='default'):
        return connections.get_connection(alias)

    @classmethod
    def get_doc_type(cls):
        return cls._doc_type.name

    @classmethod
    def case_insensitive_keywords(cls, keywords):
        '''Create a unique list of lowercased keywords.'''
        return sorted(set([keyword.lower() for keyword in keywords]))

    @classmethod
    def from_django(cls, obj):
        is_root_document = obj.slug.count('/') == 1
        doc = {
            'id': obj.id,
            'boost': 4.0 if is_root_document else 1.0,
            'title': obj.title,
            'slug': obj.slug,
            'summary': obj.get_summary_text(),
            'locale': obj.locale,
            'modified': obj.modified,
            'content': strip_tags(obj.rendered_html or ''),
            'tags': [o.name for o in obj.tags.all()],
            'kumascript_macros': cls.case_insensitive_keywords(
                obj.extract.macro_names()),
            'css_classnames': cls.case_insensitive_keywords(
                obj.extract.css_classnames()),
            'html_attributes': cls.case_insensitive_keywords(
                obj.extract.html_attributes()),
        }

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
        options = {
            'using': connections.get_connection(),
            'index': cls.get_index(),
            'doc_type': {cls._doc_type.name: cls.from_es},
        }
        options.update(kwargs)
        sq = Search(**options)

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
                   .filter(is_redirect=False)
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
        return (not obj.is_redirect and
                not any([exclude in obj.slug
                         for exclude in cls.exclude_slugs]))

    def get_excerpt(self):
        highlighted = getattr(self.meta, 'highlight', None)
        if highlighted:
            for excerpt_field in self.excerpt_fields:
                if excerpt_field in highlighted:
                    return u'…'.join(highlighted[excerpt_field])
        return self.summary

    @classmethod
    def reindex_all(cls, chunk_size=500, index=None, percent=100):
        """Rebuild ElasticSearch indexes.

        :arg chunk_size: how many documents to bulk index as a single chunk.
        :arg index: the `Index` object to reindex into. Uses the current
            promoted index if none provided.
        :arg percent: 1 to 100--the percentage of the db to index.

        """
        from kuma.search.models import Index
        from kuma.search.tasks import prepare_index, finalize_index
        from kuma.wiki.tasks import index_documents

        index = index or Index.objects.get_current()

        # Get the list of document IDs to index.
        indexable = WikiDocumentType.get_indexable(percent)

        total = len(indexable)
        total_chunks = int(ceil(total / chunk_size))

        pre_task = prepare_index.si(index.pk)
        post_task = finalize_index.si(index.pk)

        if not total:
            # If there's no data we still create the index and finalize it.
            chain(pre_task, post_task).apply_async()
        else:
            index_tasks = [index_documents.si(chunk, index.pk)
                           for chunk in chunked(indexable, chunk_size)]
            chord_flow(pre_task, index_tasks, post_task).apply_async()

        message = _(
            'Indexing %(total)d documents into %(total_chunks)d chunks of '
            'size %(size)d into index %(index)s.' % {
                'total': total,
                'total_chunks': total_chunks,
                'size': chunk_size,
                'index': index.prefixed_name
            }
        )
        return message
