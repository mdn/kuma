from datetime import datetime

from django.core import serializers
from django.core.cache import get_cache
from django.db import models

import bleach
import constance.config

from .constants import (ALLOWED_TAGS, ALLOWED_ATTRIBUTES, ALLOWED_STYLES,
                        SECONDARY_CACHE_ALIAS, TEMPLATE_TITLE_PREFIX,
                        URL_REMAPS_CACHE_KEY_TMPL)
from .content import parse as parse_content
from .queries import TransformQuerySet


class TransformManager(models.Manager):

    def get_query_set(self):
        return TransformQuerySet(self.model)


class BaseDocumentManager(models.Manager):
    """Manager for Documents, assists for queries"""
    def clean_content(self, content_in, use_constance_bleach_whitelists=False):
        allowed_hosts = constance.config.KUMA_WIKI_IFRAME_ALLOWED_HOSTS
        out = (parse_content(content_in)
               .filterIframeHosts(allowed_hosts)
               .serialize())

        if use_constance_bleach_whitelists:
            tags = constance.config.BLEACH_ALLOWED_TAGS
            attributes = constance.config.BLEACH_ALLOWED_ATTRIBUTES
            styles = constance.config.BLEACH_ALLOWED_STYLES
        else:
            tags = ALLOWED_TAGS
            attributes = ALLOWED_ATTRIBUTES
            styles = ALLOWED_STYLES

        out = bleach.clean(out, attributes=attributes, tags=tags,
                           styles=styles, skip_gauntlet=True)
        return out

    def get_by_natural_key(self, locale, slug):
        return self.get(locale=locale, slug=slug)

    def get_by_stale_rendering(self):
        """Find documents whose renderings have gone stale"""
        return (self.exclude(render_expires__isnull=True)
                    .filter(render_expires__lte=datetime.now()))

    def allows_add_by(self, user, slug):
        """Determine whether the user can create a document with the given
        slug. Mainly for enforcing Template: editing permissions"""
        if (slug.startswith(TEMPLATE_TITLE_PREFIX) and
                not user.has_perm('wiki.add_template_document')):
            return False
        # NOTE: We could enforce wiki.add_document here, but it's implicitly
        # assumed everyone is allowed.
        return True

    def filter_for_list(self, locale=None, category=None, tag=None,
                        tag_name=None, errors=None, noparent=None,
                        toplevel=None):
        docs = (self.filter(is_template=False, is_redirect=False)
                    .exclude(slug__startswith='User:')
                    .exclude(slug__startswith='Talk:')
                    .exclude(slug__startswith='User_talk:')
                    .exclude(slug__startswith='Template_talk:')
                    .exclude(slug__startswith='Project_talk:')
                    .order_by('slug'))
        if locale:
            docs = docs.filter(locale=locale)
        if category:
            try:
                docs = docs.filter(category=int(category))
            except ValueError:
                pass
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
        bq = 'current_revision__review_tags__%s'
        if tag_name:
            query = {bq % 'name': tag_name}
        elif tag:
            query = {bq % 'in': [tag]}
        else:
            query = {bq % 'name__isnull': False}
        if locale:
            query['locale'] = locale
        return self.filter(**query).distinct()

    def filter_with_localization_tag(self, locale=None, tag=None, tag_name=None):
        """Filter for documents with a localization tag on current revision"""
        bq = 'current_revision__localization_tags__%s'
        if tag_name:
            query = {bq % 'name': tag_name}
        elif tag:
            query = {bq % 'in': [tag]}
        else:
            query = {bq % 'name__isnull': False}
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
            'parent', 'parent_topic', 'category', 'document', 'is_redirect',
            'summary', 'content', 'comment',
            'keywords', 'tags', 'toc_depth', 'is_approved',
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
    def get_query_set(self):
        return super(DocumentManager, self).get_query_set().filter(deleted=False)


class DeletedDocumentManager(BaseDocumentManager):
    """
    Specialized manager for working with deleted pages.
    """
    def get_query_set(self):
        return super(DeletedDocumentManager, self).get_query_set().filter(deleted=True)


class DocumentAdminManager(BaseDocumentManager):
    """
    A manager used only in the admin site, which does not perform any
    filtering based on deleted status.
    """


class TaggedDocumentManager(models.Manager):
    def get_query_set(self):
        base_qs = super(TaggedDocumentManager, self).get_query_set()
        return base_qs.filter(content_object__deleted=False)


class DocumentZoneManager(models.Manager):
    """Manager for DocumentZone objects"""

    def get_url_remaps(self, locale):
        cache_key = URL_REMAPS_CACHE_KEY_TMPL % locale
        s_cache = get_cache(SECONDARY_CACHE_ALIAS)
        remaps = s_cache.get(cache_key)

        if not remaps:
            qs = (self.filter(document__locale=locale,
                              url_root__isnull=False)
                      .exclude(url_root=''))
            remaps = [{
                'original_path': '/docs/%s' % zone.document.slug,
                'new_path': '/%s' % zone.url_root
            } for zone in qs]
            s_cache.set(cache_key, remaps)

        return remaps


class AttachmentManager(models.Manager):

    def allow_add_attachment_by(self, user):
        """Returns whether the `user` is allowed to upload attachments.

        This is determined by a negative permission, `disallow_add_attachment`
        When the user has this permission, upload is disallowed unless it's
        a superuser or staff.
        """
        if user.is_superuser or user.is_staff:
            # Superusers and staff always allowed
            return True
        if user.has_perm('wiki.add_attachment'):
            # Explicit add permission overrides disallow
            return True
        if user.has_perm('wiki.disallow_add_attachment'):
            # Disallow generally applied via group, so per-user allow can
            # override
            return False
        return True
