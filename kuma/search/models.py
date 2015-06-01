# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify

from elasticsearch.exceptions import NotFoundError
from taggit.managers import TaggableManager

from kuma.core.urlresolvers import reverse
from kuma.wiki.search import WikiDocumentType

from .jobs import AvailableFiltersJob
from .managers import IndexManager, FilterManager


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

    def delete_if_exists(self):
        es = WikiDocumentType.get_connection()
        try:
            es.indices.delete(self.prefixed_name)
        except NotFoundError:
            # Can ignore this since it indicates the index doesn't exist
            # and therefore there's nothing to delete.
            pass

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
        return WikiDocumentType.reindex_all(index=self, chunk_size=500)

    def record_outdated(self, instance):
        if self.successor:
            return OutdatedObject.objects.create(index=self.successor,
                                                 content_object=instance)

    def promote(self):
        from kuma.wiki.tasks import index_documents

        # Index all outdated documents to this index.
        outdated_ids = []
        for outdated_object in self.outdated_objects.all():
            instance = outdated_object.content_object
            outdated_ids.append(instance.id)
        if outdated_ids:
            index_documents.delay(outdated_ids, self.pk)
        # Clear outdated.
        self.outdated_objects.all().delete()
        # Promote this index.
        self.promoted = True
        self.save()
        # Allow only a single index to be promoted.
        Index.objects.exclude(pk=self.pk).update(promoted=False)

    def demote(self):
        self.promoted = False
        self.save()


@receiver(models.signals.post_delete,
          sender=Index, dispatch_uid='search.index.delete')
def delete_index(**kwargs):
    index = kwargs.get('instance', None)
    if index is not None:
        index.delete_if_exists()


class OutdatedObject(models.Model):
    index = models.ForeignKey(Index, related_name='outdated_objects')
    created_at = models.DateTimeField(default=timezone.now)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


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
        OPERATOR_OR: 'or',
        OPERATOR_AND: 'and',
    }
    name = models.CharField(max_length=255, db_index=True,
                            help_text='the English name of the filter '
                                      'to be shown in the frontend UI')
    slug = models.CharField(max_length=255, db_index=True,
                            help_text='the slug to be used as a query '
                                      'parameter in the search URL')
    shortcut = models.CharField(max_length=255, db_index=True,
                                null=True, blank=True,
                                help_text='the name of the shortcut to '
                                          'show in the command and query UI. '
                                          'e.g. fxos')
    group = models.ForeignKey(FilterGroup, related_name='filters',
                              help_text='E.g. "Topic", "Skill level" etc')
    tags = TaggableManager(help_text='A comma-separated list of tags. '
                                     'If more than one tag given a OR '
                                     'query is executed')
    operator = models.CharField(max_length=3, choices=OPERATOR_CHOICES,
                                default=OPERATOR_OR,
                                help_text='The logical operator to use '
                                          'if more than one tag is given')
    enabled = models.BooleanField(default=True,
                                  help_text='Whether this filter is shown '
                                            'to users or not.')
    visible = models.BooleanField(default=True,
                                  help_text='Whether this filter is shown '
                                            'at public places, e.g. the '
                                            'command and query UI')

    objects = FilterManager()

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


@receiver(models.signals.post_save, sender=Filter)
@receiver(models.signals.pre_delete, sender=Filter)
def invalidate_filter_cache(sender, instance, **kwargs):
    AvailableFiltersJob().invalidate()
