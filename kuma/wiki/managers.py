from datetime import date, datetime, timedelta

from django.core import serializers
from django.db import models

import bleach
from constance import config
from django_mysql.models import QuerySet

from .constants import (ALLOWED_TAGS, ALLOWED_ATTRIBUTES, ALLOWED_STYLES,
                        TEMPLATE_TITLE_PREFIX)
from .content import parse as parse_content
from .queries import TransformQuerySet


class TransformManager(models.Manager):

    def get_queryset(self):
        return TransformQuerySet(self.model)


class BaseDocumentManager(models.Manager):
    """Manager for Documents, assists for queries"""
    def get_queryset(self):
        return QuerySet(self.model)

    def clean_content(self, content_in, use_constance_bleach_whitelists=False):
        allowed_hosts = config.KUMA_WIKI_IFRAME_ALLOWED_HOSTS
        blocked_protocols = config.KUMA_WIKI_HREF_BLOCKED_PROTOCOLS
        out = (parse_content(content_in)
               .filterIframeHosts(allowed_hosts)
               .filterAHrefProtocols(blocked_protocols)
               .serialize())

        if use_constance_bleach_whitelists:
            tags = config.BLEACH_ALLOWED_TAGS
            attributes = config.BLEACH_ALLOWED_ATTRIBUTES
            styles = config.BLEACH_ALLOWED_STYLES
        else:
            tags = ALLOWED_TAGS
            attributes = ALLOWED_ATTRIBUTES
            styles = ALLOWED_STYLES

        return bleach.clean(out, attributes=attributes, tags=tags,
                            styles=styles)

    def get_by_natural_key(self, locale, slug):
        return self.get(locale=locale, slug=slug)

    def get_by_stale_rendering(self):
        """Find documents whose renderings have gone stale"""
        return (self.exclude(render_expires__isnull=True)
                    .filter(render_expires__lte=datetime.now()))

    def allows_add_by(self, user, slug):
        """
        Determine whether the user can create a document with the given
        slug. Mainly for enforcing Template: editing permissions

        TODO: Convert to a method that raises exceptions that are handled
        by an exception middleware.
        """
        if (slug.startswith(TEMPLATE_TITLE_PREFIX) and
                not user.has_perm('wiki.add_template_document')):
            return False
        # TODO: Add wiki.add_document check
        return True

    def filter_for_list(self, locale=None, tag=None, tag_name=None,
                        errors=None, noparent=None, toplevel=None):
        docs = (self.filter(is_template=False, is_redirect=False)
                    .exclude(slug__startswith='User:')
                    .exclude(slug__startswith='Talk:')
                    .exclude(slug__startswith='User_talk:')
                    .exclude(slug__startswith='Template_talk:')
                    .exclude(slug__startswith='Project_talk:')
                    .order_by('slug'))
        if locale:
            docs = docs.filter(locale=locale)
        if tag:
            docs = docs.filter(tags__in=[tag])
        if tag_name:
            docs = docs.filter(tags__name=tag_name)
        if errors:
            docs = (docs.exclude(rendered_errors__isnull=True)
                        .exclude(rendered_errors__exact='[]'))
        if noparent:
            # List translated pages without English source associated
            docs = docs.filter(parent__isnull=True)
        if toplevel:
            docs = docs.filter(parent_topic__isnull=True)

        # Leave out the html, since that leads to huge cache objects and we
        # never use the content in lists.
        docs = docs.defer('html')
        return docs

    def filter_for_review(self, locale=None, tag=None, tag_name=None):
        """Filter for documents with current revision flagged for review"""
        query = 'current_revision__review_tags__%s'
        if tag_name:
            query = {query % 'name': tag_name}
        elif tag:
            query = {query % 'in': [tag]}
        else:
            query = {query % 'name__isnull': False}
        if locale:
            query['locale'] = locale
        return self.filter(**query).distinct()

    def filter_with_localization_tag(self, locale=None, tag=None, tag_name=None):
        """Filter for documents with a localization tag on current revision"""
        query = 'current_revision__localization_tags__%s'
        if tag_name:
            query = {query % 'name': tag_name}
        elif tag:
            query = {query % 'in': [tag]}
        else:
            query = {query % 'name__isnull': False}
        if locale:
            query['locale'] = locale
        return self.filter(**query).distinct()

    def dump_json(self, queryset, stream):
        """Export a stream of JSON-serialized Documents and Revisions

        This is inspired by smuggler.views.dump_data with customizations for
        Document specifics, per bug 747137
        """
        objects = []
        for doc in queryset.all():
            rev = doc.current_or_latest_revision()
            if not rev:
                # Skip this doc if, for some reason, there's no revision.
                continue

            # Drop the pk and circular reference to rev.
            doc.pk = None
            doc.current_revision = None
            objects.append(doc)

            # Drop the rev pk
            rev.pk = None
            objects.append(rev)

        # HACK: This is kind of awkward, but the serializer only accepts a flat
        # list of field names across all model classes that get handled. So,
        # this is a mashup whitelist of Document and Revision fields.
        fields = (
            # TODO: Maybe make this an *exclusion* list by getting the list of
            # fields from Document and Revision models and knocking out what we
            # don't want? Serializer doesn't support exclusion list directly.
            'title', 'locale', 'slug', 'tags', 'is_template', 'is_localizable',
            'parent', 'parent_topic', 'document', 'is_redirect', 'summary',
            'content', 'comment', 'keywords', 'tags', 'toc_depth',
            'is_approved',
            'creator',  # HACK: Replaced on import, but deserialize needs it
            'is_mindtouch_migration',
        )
        serializers.serialize('json', objects, indent=2, stream=stream,
                              fields=fields, use_natural_keys=True)

    def load_json(self, creator, stream):
        """Import a stream of JSON-serialized Documents and Revisions

        This is inspired by smuggler.views.load_data with customizations for
        Document specifics, per bug 747137
        """
        counter = 0
        objects = serializers.deserialize('json', stream)
        for obj in objects:

            # HACK: Dig up the deserializer wrapped model object & manager,
            # because the deserializer wrapper bypasses some things we need to
            # un-bypass here
            actual = obj.object
            mgr = actual._default_manager

            actual.pk = None
            if hasattr(mgr, 'get_by_natural_key'):
                # If the model uses natural keys, attempt to find the pk of an
                # existing record to overwrite.
                try:
                    nk = actual.natural_key()
                    existing = mgr.get_by_natural_key(*nk)
                    actual.pk = existing.pk
                except actual.DoesNotExist:
                    pass

            # Tweak a few fields on the way through for Revisions.
            # Don't do a type check here since that would require importing
            if actual._meta.object_name == 'Revision':
                actual.creator = creator
                actual.created = datetime.now()

            actual.save()
            counter += 1

        return counter


class DocumentManager(BaseDocumentManager):
    """
    The actual manager, which filters to show only non-deleted pages.
    """
    def get_queryset(self):
        return super(DocumentManager, self).get_queryset().filter(deleted=False)


class DeletedDocumentManager(BaseDocumentManager):
    """
    Specialized manager for working with deleted pages.
    """
    def get_queryset(self):
        return super(DeletedDocumentManager, self).get_queryset().filter(deleted=True)


class DocumentAdminManager(BaseDocumentManager):
    """
    A manager used only in the admin site, which does not perform any
    filtering based on deleted status.
    """


class TaggedDocumentManager(models.Manager):
    def get_queryset(self):
        base_qs = super(TaggedDocumentManager, self).get_queryset()
        return base_qs.filter(content_object__deleted=False)


class RevisionIPManager(models.Manager):

    def delete_old(self, days=30):
        cutoff_date = date.today() - timedelta(days=days)
        old_rev_ips = self.filter(revision__created__lte=cutoff_date)
        old_rev_ips.delete()

    def log(self, revision, headers, data):
        """
        Records the IP and some more data for the given revision and the
        request headers.
        """
        self.create(
            revision=revision,
            ip=headers.get('REMOTE_ADDR'),
            user_agent=headers.get('HTTP_USER_AGENT', ''),
            referrer=headers.get('HTTP_REFERER', ''),
            data=data
        )
