# -*- coding: utf-8 -*-
import operator
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.db.models.signals import post_delete
from django.utils.html import strip_tags
from django.utils import timezone
from django.utils.functional import cached_property
from django.template.defaultfilters import slugify

from elasticutils.contrib.django import MappingType, Indexable
from elasticutils.contrib.django.tasks import index_objects

from sumo.urlresolvers import reverse

from wiki.models import Document
from taggit_extras.managers import PrefetchTaggableManager

from .decorators import register_mapping_type
from .queries import DocumentS
from .signals import delete_index


class IndexManager(models.Manager):
    """
    The model manager to implement a couple of useful methods for handling
    search indexes.
    """
    def get_current(self):
        try:
            return (self.filter(promoted=True, populated=True)
                        .order_by('-created_at'))[0]
        except (self.model.DoesNotExist, IndexError, AttributeError):
            fallback_name = settings.ES_INDEXES['default']
            return Index(name=fallback_name, populated=True, promoted=True)


class Index(models.Model):
    """
    Model to store a bunch of metadata about search indexes including
    a way to promote it to be picked up as the "current" one.
    """
    created_at = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=30, blank=True, null=True,
                            help_text='The search index name, set to '
                                      'the created date when left empty')
    promoted = models.BooleanField(default=False)
    populated = models.BooleanField(default=False)

    objects = IndexManager()

    class Meta:
        verbose_name = 'Index'
        verbose_name_plural = 'Indexes'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.created_at.strftime('%Y-%m-%d-%H-%M-%S')
        super(Index, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    @cached_property
    def successor(self):
        try:
            return self.get_next_by_created_at()
        except (Index.DoesNotExist, ValueError):
            return None

    @cached_property
    def prefixed_name(self):
        "The name to use for the search index in ES"
        return '%s-%s' % (settings.ES_INDEX_PREFIX, self.name)

    def populate(self):
        from .tasks import populate_index
        populate_index.delay(self.pk)

    def record_outdated(self, instance):
        if self.successor:
            return OutdatedObject.objects.create(index=self.successor,
                                                 content_object=instance)

    def promote(self):
        rescheduled = []
        for outdated_object in self.outdated_objects.all():
            instance = outdated_object.content_object
            label = ('%s.%s.%s' %
                     (outdated_object.content_type.natural_key() +
                      (instance.id,)))  # gives us 'wiki.document.12345'
            if label in rescheduled:
                continue
            mappping_type = instance.get_mapping_type()
            index_objects.delay(mappping_type, [instance.id])
            rescheduled.append(label)
        self.outdated_objects.all().delete()
        self.promoted = True
        self.save()

    def demote(self):
        self.promoted = False
        self.save()


post_delete.connect(delete_index, sender=Index,
                    dispatch_uid='search.index.delete')


class OutdatedObject(models.Model):
    index = models.ForeignKey(Index, related_name='outdated_objects')
    created_at = models.DateTimeField(default=timezone.now)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')


class FilterGroup(models.Model):
    """
    A way to group different kinds of filters from each other.
    """
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True,
                            help_text='the slug to be used as the name of the '
                                      'query parameter in the search URL')
    order = models.IntegerField(default=1,
                                help_text='An integer defining which order '
                                          'the filter group should show up '
                                          'in the sidebar')

    class Meta:
        ordering = ('-order', 'name')
        unique_together = (
            ('name', 'slug'),
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(FilterGroup, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class Filter(models.Model):
    """
    The model to store custom search filters in the database. This is
    used to dynamically tweak the search filters available to users.
    """
    OPERATOR_AND = 'AND'
    OPERATOR_OR = 'OR'
    OPERATOR_CHOICES = (
        (OPERATOR_OR, OPERATOR_OR),
        (OPERATOR_AND, OPERATOR_AND),
    )
    OPERATORS = {
        OPERATOR_OR: operator.or_,
        OPERATOR_AND: operator.and_,
    }
    name = models.CharField(max_length=255, db_index=True,
                            help_text='the English name of the filter '
                                      'to be shown in the frontend UI')
    slug = models.CharField(max_length=255, db_index=True,
                            help_text='the slug to be used as a query '
                                      'parameter in the search URL')
    group = models.ForeignKey(FilterGroup, related_name='filters',
                              help_text='E.g. "Topic", "Skill level" etc')
    tags = PrefetchTaggableManager(help_text='A comma-separated list of tags. '
                                             'If more than one tag given a OR '
                                             'query is executed')
    operator = models.CharField(max_length=3, choices=OPERATOR_CHOICES,
                                default=OPERATOR_OR,
                                help_text='The logical operator to use '
                                          'if more than one tag is given')
    enabled = models.BooleanField(default=True,
                                  help_text='Whether this filter is shown '
                                            'to users or not.')

    class Meta(object):
        unique_together = (
            ('name', 'slug'),
        )

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        path = reverse('search', locale=settings.LANGUAGE_CODE)
        return '%s%s?%s=%s' % (settings.SITE_URL, path,
                               self.group.slug, self.slug)


@register_mapping_type
class DocumentType(MappingType, Indexable):
    excerpt_fields = ['summary', 'content']
    exclude_slugs = ['Talk:', 'User:', 'User_talk:', 'Template_talk:',
                     'Project_talk:']

    @classmethod
    def get_model(cls):
        return Document

    @classmethod
    def get_index(cls):
        return Index.objects.get_current().prefixed_name

    @classmethod
    def search(cls):
        """Returns a typed S for this class.

        :returns: an `S` for this DjangoMappingType

        """
        return DocumentS(cls)

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
                # word delimiter filter and the elision filter#
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
                'caseInsensitiveKeyword': {
                    'type': 'custom',
                    'tokenizer': 'keyword',
                    'filter': 'lowercase'
                }
            },
        }

    @classmethod
    def get_mapping(cls):
        return {
            # try to not waste so much space
            '_all': {'enabled': False},
            '_boost': {'name': '_boost', 'null_value': 1.0, 'type': 'float'},
            'content': {
                'type': 'string',
                'analyzer': 'kuma_content',
                # faster highlighting
                'term_vector': 'with_positions_offsets',
            },
            'id': {'type': 'long', 'index': 'not_analyzed'},
            'locale': {'type': 'string', 'index': 'not_analyzed'},
            'modified': {'type': 'date'},
            'slug': {'type': 'string', 'index': 'not_analyzed'},
            'summary': {
                'type': 'string',
                'analyzer': 'kuma_content',
                # faster highlighting
                'term_vector': 'with_positions_offsets',
            },
            'tags': {'type': 'string', 'analyzer': 'case_sensitive'},
            'title': {
                'type': 'string',
                'analyzer': 'kuma_title',
                'boost': 1.2,  # the title usually has the best description
            },
            'kumascript_macros': {
                'type': 'string',
                'analyzer': 'caseInsensitiveKeyword'
            },
            'css_classnames': {
                'type': 'string',
                'analyzer': 'caseInsensitiveKeyword'
            },
            'html_attributes': {
                'type': 'string',
                'analyzer': 'caseInsensitiveKeyword'
            },
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        if obj is None:
            obj = cls.get_model().objects.get(pk=obj_id)

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
            doc['_boost'] = 8.0
        elif obj.slug.split('/') == 1:
            # a little boost if no zone but still first level
            doc['_boost'] = 4.0
        else:
            doc['_boost'] = 1.0

        return doc

    @classmethod
    def get_indexable(cls):
        """
        For this mapping type return a list of model IDs that should be
        indexed with the management command, in a full reindex.

        WARNING: When changing this code make sure to update the
                 ``should_update`` method below, too!
        """
        model = cls.get_model()

        excludes = []
        for exclude in cls.exclude_slugs:
            excludes.append(models.Q(slug__icontains=exclude))

        return (model.objects
                     .filter(is_template=False,
                             is_redirect=False,
                             deleted=False)
                     .exclude(reduce(operator.or_, excludes))
                     .values_list('id', flat=True))

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
        for field in self.excerpt_fields:
            if field in self._highlight:
                return u'…'.join(self._highlight[field])
        return self.summary

    def get_url(self):
        path = reverse('wiki.document', locale=self.locale, args=[self.slug])
        return '%s%s' % (settings.SITE_URL, path)

    def get_edit_url(self):
        path = reverse('wiki.edit_document', locale=self.locale,
                       args=[self.slug])
        return '%s%s' % (settings.SITE_URL, path)
