import hashlib
import json
import sys
import traceback
from datetime import datetime, timedelta
from functools import wraps
from uuid import uuid4

import newrelic.agent
import waffle
from constance import config
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import signals
from django.utils.decorators import available_attrs
from django.utils.functional import cached_property
from django.utils.translation import ugettext, ugettext_lazy as _
from pyquery import PyQuery
from taggit.managers import TaggableManager
from taggit.models import ItemBase, TagBase
from taggit.utils import edit_string_for_tags, parse_tags
from tidings.models import NotificationsMixin

from kuma.core.cache import memcache
from kuma.core.exceptions import ProgrammingError
from kuma.core.i18n import get_language_mapping
from kuma.core.urlresolvers import reverse
from kuma.search.decorators import register_live_index
from kuma.spam.models import AkismetSubmission, SpamAttempt

from . import kumascript
from .constants import (DEKI_FILE_URL, DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL,
                        KUMA_FILE_URL, REDIRECT_CONTENT, REDIRECT_HTML,
                        TEMPLATE_TITLE_PREFIX)
from .content import parse as parse_content
from .content import (Extractor, H2TOCFilter, H3TOCFilter, SectionTOCFilter,
                      get_content_sections, get_seo_description)
from .exceptions import (DocumentRenderedContentNotAvailable,
                         DocumentRenderingInProgress, PageMoveError,
                         SlugCollision, UniqueCollision)
from .jobs import DocumentContributorsJob, DocumentZoneStackJob
from .managers import (DeletedDocumentManager, DocumentAdminManager,
                       DocumentManager, RevisionIPManager,
                       TaggedDocumentManager, TransformManager)
from .signals import render_done
from .templatetags.jinja_helpers import absolutify
from .utils import tidy_content


def cache_with_field(field_name):
    """Decorator for generated content methods.

    If the backing model field is null, or kwarg force_fresh is True, call the
    decorated method to generate and return the content.

    Otherwise, just return the value in the backing model field.
    """
    def decorator(fn):
        @wraps(fn, assigned=available_attrs(fn))
        def wrapper(self, *args, **kwargs):
            force_fresh = kwargs.pop('force_fresh', False)

            # Try getting the value using the DB field.
            field_val = getattr(self, field_name)
            if field_val is not None and not force_fresh:
                return field_val

            # DB field is blank, or we're forced to generate it fresh.
            field_val = fn(self, force_fresh=force_fresh)
            setattr(self, field_name, field_val)
            return field_val

        return wrapper
    return decorator


def _inherited(parent_attr, direct_attr):
    """Return a descriptor delegating to an attr of the original document.

    If `self` is a translation, the descriptor delegates to the attribute
    `parent_attr` from the original document. Otherwise, it delegates to the
    attribute `direct_attr` from `self`.

    Use this only on a reference to another object, like a ManyToMany or a
    ForeignKey. Using it on a normal field won't work well, as it'll preclude
    the use of that field in QuerySet field lookups. Also, ModelForms that are
    passed instance=this_obj won't see the inherited value.

    """
    getter = lambda self: (getattr(self.parent, parent_attr)
                           if self.parent and self.parent.id != self.id
                           else getattr(self, direct_attr))
    setter = lambda self, val: (setattr(self.parent, parent_attr, val)
                                if self.parent and self.parent.id != self.id
                                else setattr(self, direct_attr, val))
    return property(getter, setter)


def valid_slug_parent(slug, locale):
    slug_bits = slug.split('/')
    slug_bits.pop()
    parent = None
    if slug_bits:
        parent_slug = '/'.join(slug_bits)
        try:
            parent = Document.objects.get(locale=locale, slug=parent_slug)
        except Document.DoesNotExist:
            raise Exception(
                ugettext('Parent %s does not exist.' % (
                    '%s/%s' % (locale, parent_slug))))

    return parent


class DocumentTag(TagBase):
    """A tag indexing a document"""
    class Meta:
        verbose_name = _('Document Tag')
        verbose_name_plural = _('Document Tags')


def tags_for(cls, model, instance=None, **extra_filters):
    """
    Sadly copied from taggit to work around the issue of not being
    able to use the TaggedItemBase class that has tag field already
    defined.
    """
    kwargs = extra_filters or {}
    if instance is not None:
        kwargs.update({
            '%s__content_object' % cls.tag_relname(): instance
        })
        return cls.tag_model().objects.filter(**kwargs)
    kwargs.update({
        '%s__content_object__isnull' % cls.tag_relname(): False
    })
    return cls.tag_model().objects.filter(**kwargs).distinct()


class TaggedDocument(ItemBase):
    """Through model, for tags on Documents"""
    content_object = models.ForeignKey('Document')
    tag = models.ForeignKey(DocumentTag, related_name="%(app_label)s_%(class)s_items")

    objects = TaggedDocumentManager()

    @classmethod
    def tags_for(cls, *args, **kwargs):
        return tags_for(cls, *args, **kwargs)


class DocumentAttachment(models.Model):
    """
    Intermediary between Documents and Attachments. Allows storing the
    user who attached a file to a document, and a (unique for that
    document) name for referring to the file from the document.
    """
    file = models.ForeignKey(
        'attachments.Attachment',
        related_name='document_attachments',
    )
    document = models.ForeignKey(
        'wiki.Document',
        related_name='attached_files',
    )
    attached_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    name = models.TextField()

    # whether or not this attachment was uploaded for the document
    is_original = models.BooleanField(
        verbose_name=_('uploaded to the document'),
        default=False,
    )

    # whether or not this attachment is linked in the document's content
    is_linked = models.BooleanField(
        verbose_name=_('linked in the document content'),
        default=False,
    )

    class Meta:
        db_table = 'attachments_documentattachment'

    def __unicode__(self):
        return u'"%s" for document "%s"' % (self.file, self.document)

    def clean(self):
        if self.pk and (self.document.files.through.objects.exclude(pk=self.pk)
                                                           .exists()):
            raise ValidationError(
                _("Attachment %(attachment_id)s can't be attached "
                  "multiple times to document %(document_id)s") %
                {'attachment_id': self.pk, 'document_id': self.document.pk}
            )


@register_live_index
class Document(NotificationsMixin, models.Model):
    """A localized knowledgebase document, not revision-specific."""
    TOC_FILTERS = {
        1: SectionTOCFilter,
        2: H2TOCFilter,
        3: H3TOCFilter,
        4: SectionTOCFilter
    }

    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # NOTE: Documents are indexed by tags, but tags are edited in Revisions.
    # Also, using a custom through table to isolate Document tags from those
    # used in other models and apps. (Works better than namespaces, for
    # completion and such.)
    tags = TaggableManager(through=TaggedDocument)

    # Is this document a template or not?
    is_template = models.BooleanField(default=False, editable=False,
                                      db_index=True)

    # Is this a redirect or not?
    is_redirect = models.BooleanField(default=False, editable=False,
                                      db_index=True)

    # Is this document localizable or not?
    is_localizable = models.BooleanField(default=True, db_index=True)

    locale = models.CharField(
        max_length=7,
        choices=settings.LANGUAGES,
        default=settings.WIKI_DEFAULT_LANGUAGE,
        db_index=True,
    )

    # Latest approved revision. L10n dashboard depends on this being so (rather
    # than being able to set it to earlier approved revisions).
    current_revision = models.ForeignKey(
        'Revision',
        null=True,
        related_name='current_for+',
    )

    # The Document I was translated from. NULL if this doc is in the default
    # locale or it is nonlocalizable. TODO: validate against
    # settings.WIKI_DEFAULT_LANGUAGE.
    parent = models.ForeignKey(
        'self',
        related_name='translations',
        null=True,
        blank=True,
    )

    parent_topic = models.ForeignKey(
        'self',
        related_name='children',
        null=True,
        blank=True,
    )

    # The files attached to the document, represented by a custom intermediate
    # model so we can store some metadata about the relation
    files = models.ManyToManyField(
        'attachments.Attachment',
        through=DocumentAttachment,
    )

    # JSON representation of Document for API results, built on save
    json = models.TextField(editable=False, blank=True, null=True)

    # Raw HTML of approved revision's wiki markup
    html = models.TextField(editable=False)

    # Cached result of kumascript and other offline processors (if any)
    rendered_html = models.TextField(editable=False, blank=True, null=True)

    # Errors (if any) from the last rendering run
    rendered_errors = models.TextField(editable=False, blank=True, null=True)

    # Whether or not to automatically defer rendering of this page to a queued
    # offline task. Generally used for complex pages that need time
    defer_rendering = models.BooleanField(default=False, db_index=True)

    # Timestamp when this document was last scheduled for a render
    render_scheduled_at = models.DateTimeField(null=True, db_index=True)

    # Timestamp when a render for this document was last started
    render_started_at = models.DateTimeField(null=True, db_index=True)

    # Timestamp when this document was last rendered
    last_rendered_at = models.DateTimeField(null=True, db_index=True)

    # Maximum age (in seconds) before this document needs re-rendering
    render_max_age = models.IntegerField(blank=True, null=True)

    # Time after which this document needs re-rendering
    render_expires = models.DateTimeField(blank=True, null=True, db_index=True)

    # Whether this page is deleted.
    deleted = models.BooleanField(default=False, db_index=True)

    # Last modified time for the document. Should be equal-to or greater than
    # the current revision's created field
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    body_html = models.TextField(editable=False, blank=True, null=True)

    quick_links_html = models.TextField(editable=False, blank=True, null=True)

    zone_subnav_local_html = models.TextField(editable=False,
                                              blank=True, null=True)

    toc_html = models.TextField(editable=False, blank=True, null=True)

    summary_html = models.TextField(editable=False, blank=True, null=True)

    summary_text = models.TextField(editable=False, blank=True, null=True)

    uuid = models.UUIDField(default=uuid4, editable=False)

    class Meta(object):
        unique_together = (
            ('parent', 'locale'),
            ('slug', 'locale'),
        )
        permissions = (
            ('view_document', 'Can view document'),
            ('add_template_document', 'Can add Template:* document'),
            ('change_template_document', 'Can change Template:* document'),
            ('move_tree', 'Can move a tree of documents'),
            ('purge_document', 'Can permanently delete document'),
            ('restore_document', 'Can restore deleted document'),
        )

    objects = DocumentManager()
    deleted_objects = DeletedDocumentManager()
    admin_objects = DocumentAdminManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.get_absolute_url(), self.title)

    @cache_with_field('body_html')
    def get_body_html(self, *args, **kwargs):
        html = self.rendered_html and self.rendered_html or self.html
        sections_to_hide = ('Quick_Links', 'Subnav')
        doc = parse_content(html)
        for sid in sections_to_hide:
            doc = doc.replaceSection(sid, '<!-- -->')
        doc.injectSectionIDs()
        doc.annotateLinks(base_url=settings.SITE_URL)
        return doc.serialize()

    @cache_with_field('quick_links_html')
    def get_quick_links_html(self, *args, **kwargs):
        return self.get_section_content('Quick_Links')

    @cache_with_field('zone_subnav_local_html')
    def get_zone_subnav_local_html(self, *args, **kwargs):
        return self.get_section_content('Subnav')

    @cache_with_field('toc_html')
    def get_toc_html(self, *args, **kwargs):
        if not self.current_revision:
            return ''
        toc_depth = self.current_revision.toc_depth
        if not toc_depth:
            return ''
        html = self.rendered_html and self.rendered_html or self.html
        return (parse_content(html)
                .injectSectionIDs()
                .filter(self.TOC_FILTERS[toc_depth])
                .serialize())

    @cache_with_field('summary_html')
    def get_summary_html(self, *args, **kwargs):
        return self.get_summary(strip_markup=False)

    @cache_with_field('summary_text')
    def get_summary_text(self, *args, **kwargs):
        return self.get_summary(strip_markup=True)

    def regenerate_cache_with_fields(self):
        """Regenerate fresh content for all the cached fields"""
        # TODO: Maybe @cache_with_field can build a registry over which this
        # method can iterate?
        self.get_body_html(force_fresh=True)
        self.get_quick_links_html(force_fresh=True)
        self.get_zone_subnav_local_html(force_fresh=True)
        self.get_toc_html(force_fresh=True)
        self.get_summary_html(force_fresh=True)
        self.get_summary_text(force_fresh=True)

    def get_zone_subnav_html(self):
        """
        Search from self up through DocumentZone stack, returning the first
        zone nav HTML found.
        """
        src = self.get_zone_subnav_local_html()
        if src:
            return src
        for zone in DocumentZoneStackJob().get(self.pk):
            src = zone.document.get_zone_subnav_local_html()
            if src:
                return src

    def get_section_content(self, section_id, ignore_heading=True):
        """
        Convenience method to extract the rendered content for a single section
        """
        if self.rendered_html:
            content = self.rendered_html
        else:
            content = self.html
        return self.extract.section(content, section_id, ignore_heading)

    def calculate_etag(self, section_id=None):
        """Calculate an etag-suitable hash for document content or a section"""
        if not section_id:
            content = self.html
        else:
            content = self.extract.section(self.html, section_id)
        return '"%s"' % hashlib.sha1(content.encode('utf8')).hexdigest()

    def current_or_latest_revision(self):
        """Returns current revision if there is one, else the last created
        revision."""
        rev = self.current_revision
        if not rev:
            revs = self.revisions.order_by('-created')
            if revs.exists():
                rev = revs[0]
        return rev

    @property
    def is_rendering_scheduled(self):
        """Does this have a rendering scheduled?"""
        if not self.render_scheduled_at:
            return False

        # Check whether a scheduled rendering has waited for too long.  Assume
        # failure, in this case, and allow another scheduling attempt.
        timeout = config.KUMA_DOCUMENT_RENDER_TIMEOUT
        max_duration = timedelta(seconds=timeout)
        duration = datetime.now() - self.render_scheduled_at
        if duration > max_duration:
            return False

        if not self.last_rendered_at:
            return True
        return self.render_scheduled_at > self.last_rendered_at

    @property
    def is_rendering_in_progress(self):
        """Does this have a rendering in progress?"""
        if not self.render_started_at:
            # No start time, so False.
            return False

        # Check whether an in-progress rendering has gone on for too long.
        # Assume failure, in this case, and allow another rendering attempt.
        timeout = config.KUMA_DOCUMENT_RENDER_TIMEOUT
        max_duration = timedelta(seconds=timeout)
        duration = datetime.now() - self.render_started_at
        if duration > max_duration:
            return False

        if not self.last_rendered_at:
            # No rendering ever, so in progress.
            return True

        # Finally, if the render start is more recent than last completed
        # render, then we have one in progress.
        return self.render_started_at > self.last_rendered_at

    @newrelic.agent.function_trace()
    def get_rendered(self, cache_control=None, base_url=None):
        """Attempt to get rendered content for this document"""
        # No rendered content yet, so schedule the first render.
        if not self.rendered_html:
            try:
                self.schedule_rendering(cache_control, base_url)
            except DocumentRenderingInProgress:
                # Unable to trigger a rendering right now, so we bail.
                raise DocumentRenderedContentNotAvailable

        # If we have a cache_control directive, try scheduling a render.
        if cache_control:
            try:
                self.schedule_rendering(cache_control, base_url)
            except DocumentRenderingInProgress:
                pass

        # Parse JSON errors, if available.
        errors = None
        try:
            errors = (self.rendered_errors and
                      json.loads(self.rendered_errors) or None)
        except ValueError:
            pass

        # If the above resulted in an immediate render, we might have content.
        if not self.rendered_html:
            if errors:
                return ('', errors)
            else:
                # But, no such luck, so bail out.
                raise DocumentRenderedContentNotAvailable

        return (self.rendered_html, errors)

    def schedule_rendering(self, cache_control=None, base_url=None):
        """
        Attempt to schedule rendering. Honor the deferred_rendering field to
        decide between an immediate or a queued render.
        """
        # Avoid scheduling a rendering if already scheduled or in progress.
        if self.is_rendering_scheduled or self.is_rendering_in_progress:
            return False

        # Note when the rendering was scheduled. Kind of a hack, doing a quick
        # update and setting the local property rather than doing a save()
        now = datetime.now()
        Document.objects.filter(pk=self.pk).update(render_scheduled_at=now)
        self.render_scheduled_at = now

        if (waffle.switch_is_active('wiki_force_immediate_rendering') or
                not self.defer_rendering):
            # Attempt an immediate rendering.
            self.render(cache_control, base_url)
        else:
            # Attempt to queue a rendering. If celery.conf.ALWAYS_EAGER is
            # True, this is also an immediate rendering.
            from . import tasks
            tasks.render_document.delay(self.pk, cache_control, base_url)

    def render(self, cache_control=None, base_url=None, timeout=None):
        """
        Render content using kumascript and any other services necessary.
        """
        if not base_url:
            base_url = settings.SITE_URL

        # Disallow rendering while another is in progress.
        if self.is_rendering_in_progress:
            raise DocumentRenderingInProgress

        # Note when the rendering was started. Kind of a hack, doing a quick
        # update and setting the local property rather than doing a save()
        now = datetime.now()
        Document.objects.filter(pk=self.pk).update(render_started_at=now)
        self.render_started_at = now

        # Perform rendering and update document
        if not config.KUMASCRIPT_TIMEOUT:
            # A timeout of 0 should shortcircuit kumascript usage.
            self.rendered_html, self.rendered_errors = self.html, []
        else:
            self.rendered_html, errors = kumascript.get(self, cache_control,
                                                        base_url,
                                                        timeout=timeout)
            self.rendered_errors = errors and json.dumps(errors) or None

        # Regenerate the cached content fields
        self.regenerate_cache_with_fields()

        # Finally, note the end time of rendering and update the document.
        self.last_rendered_at = datetime.now()

        # If this rendering took longer than we'd like, mark it for deferred
        # rendering in the future.
        timeout = config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT
        max_duration = timedelta(seconds=timeout)
        duration = self.last_rendered_at - self.render_started_at
        if duration >= max_duration:
            self.defer_rendering = True

        # TODO: Automatically clear the defer_rendering flag if the rendering
        # time falls under the limit? Probably safer to require manual
        # intervention to free docs from deferred jail.
        if self.render_max_age:
            # If there's a render_max_age, automatically update render_expires
            self.render_expires = (datetime.now() +
                                   timedelta(seconds=self.render_max_age))
        else:
            # Otherwise, just clear the expiration time as a one-shot
            self.render_expires = None

        self.save()

        render_done.send(sender=self.__class__, instance=self)

    def get_summary(self, strip_markup=True, use_rendered=True):
        """
        Attempt to get the document summary from rendered content, with
        fallback to raw HTML
        """
        if use_rendered and self.rendered_html:
            src = self.rendered_html
        else:
            src = self.html
        return get_seo_description(src, self.locale, strip_markup)

    def build_json_data(self):
        html = self.rendered_html and self.rendered_html or self.html
        content = parse_content(html).injectSectionIDs().serialize()
        sections = get_content_sections(content)

        translations = []
        if self.pk:
            for translation in self.other_translations:
                revision = translation.current_revision
                if revision.summary:
                    summary = revision.summary
                else:
                    summary = translation.get_summary(strip_markup=False)
                translations.append({
                    'last_edit': revision.created.isoformat(),
                    'locale': translation.locale,
                    'localization_tags': list(revision.localization_tags
                                                      .names()),
                    'review_tags': list(revision.review_tags.names()),
                    'summary': summary,
                    'tags': list(translation.tags.names()),
                    'title': translation.title,
                    'url': translation.get_absolute_url(),
                    'uuid': str(translation.uuid)
                })

        if self.current_revision:
            review_tags = list(self.current_revision.review_tags.names())
            localization_tags = list(self.current_revision
                                         .localization_tags
                                         .names())
            last_edit = self.current_revision.created.isoformat()
            if self.current_revision.summary:
                summary = self.current_revision.summary
            else:
                summary = self.get_summary(strip_markup=False)
        else:
            review_tags = []
            localization_tags = []
            last_edit = ''
            summary = ''

        if not self.pk:
            tags = []
        else:
            tags = list(self.tags.names())

        now_iso = datetime.now().isoformat()

        if self.modified:
            modified = self.modified.isoformat()
        else:
            modified = now_iso

        return {
            'title': self.title,
            'label': self.title,
            'url': self.get_absolute_url(),
            'id': self.id,
            'uuid': str(self.uuid),
            'slug': self.slug,
            'tags': tags,
            'review_tags': review_tags,
            'localization_tags': localization_tags,
            'sections': sections,
            'locale': self.locale,
            'summary': summary,
            'translations': translations,
            'modified': modified,
            'json_modified': now_iso,
            'last_edit': last_edit
        }

    def get_json_data(self, stale=True):
        """Returns a document in object format for output as JSON.

        The stale parameter, when True, accepts stale cached data even after
        the document has been modified."""

        # Have parsed data & don't care about freshness? Here's a quick out..
        curr_json_data = getattr(self, '_json_data', None)
        if curr_json_data and stale:
            return curr_json_data

        # Attempt to parse the current contents of self.json, taking care in
        # case it's empty or broken JSON.
        self._json_data = {}
        if self.json:
            try:
                self._json_data = json.loads(self.json)
            except (TypeError, ValueError):
                pass

        # Try to get ISO 8601 datestamps for the doc and the json
        json_lmod = self._json_data.get('json_modified', '')
        doc_lmod = self.modified.isoformat()

        # If there's no parsed data or the data is stale & we care, it's time
        # to rebuild the cached JSON data.
        if (not self._json_data) or (not stale and doc_lmod > json_lmod):
            self._json_data = self.build_json_data()
            self.json = json.dumps(self._json_data)
            Document.objects.filter(pk=self.pk).update(json=self.json)

        return self._json_data

    @cached_property
    def extract(self):
        return Extractor(self)

    def natural_key(self):
        return (self.locale, self.slug)

    @staticmethod
    def natural_key_hash(keys):
        natural_key = u'/'.join(keys)
        return hashlib.md5(natural_key.encode('utf8')).hexdigest()

    @cached_property
    def natural_cache_key(self):
        return self.natural_key_hash(self.natural_key())

    def _existing(self, attr, value):
        """Return an existing doc (if any) in this locale whose `attr` attr is
        equal to mine."""
        return Document.objects.filter(locale=self.locale, **{attr: value})

    def _raise_if_collides(self, attr, exception):
        """Raise an exception if a page of this title/slug already exists."""
        if self.id is None or hasattr(self, 'old_' + attr):
            # If I am new or my title/slug changed...
            existing = self._existing(attr, getattr(self, attr))
            if existing.exists():
                raise exception(existing[0])

    def clean(self):
        """Translations can't be localizable."""
        self._clean_is_localizable()

    def _clean_is_localizable(self):
        """is_localizable == allowed to have translations. Make sure that isn't
        violated.

        For default language (en-US), is_localizable means it can have
        translations. Enforce:
            * is_localizable=True if it has translations
            * if has translations, unable to make is_localizable=False

        For non-default langauges, is_localizable must be False.

        """
        if self.locale != settings.WIKI_DEFAULT_LANGUAGE:
            self.is_localizable = False

        # Can't save this translation if parent not localizable
        if (self.parent and self.parent.id != self.id and
                not self.parent.is_localizable):
            raise ValidationError('"%s": parent "%s" is not localizable.' % (
                                  unicode(self), unicode(self.parent)))

        # Can't make not localizable if it has translations
        # This only applies to documents that already exist, hence self.pk
        if self.pk and not self.is_localizable and self.translations.exists():
            raise ValidationError('"%s": document has %s translations but is '
                                  'not localizable.' %
                                  (unicode(self), self.translations.count()))

    def _attr_for_redirect(self, attr, template):
        """Return the slug or title for a new redirect.

        `template` is a Python string template with "old" and "number" tokens
        used to create the variant.

        """
        def unique_attr():
            """Return a variant of getattr(self, attr) such that there is no
            Document of my locale with string attribute `attr` equal to it.

            Never returns the original attr value.

            """
            # "My God, it's full of race conditions!"
            i = 1
            while True:
                new_value = template % dict(old=getattr(self, attr), number=i)
                if not self._existing(attr, new_value).exists():
                    return new_value
                i += 1

        old_attr = 'old_' + attr
        if hasattr(self, old_attr):
            # My slug (or title) is changing; we can reuse it for the redirect.
            return getattr(self, old_attr)
        else:
            # Come up with a unique slug (or title):
            return unique_attr()

    def revert(self, revision, user, comment=None):
        """
        Reverts the given revision by creating a new one.

        - Sets its comment to the given value and points the new revision
          to the old revision
        - Keeps review tags
        - Make new revision the current one of the document
        """
        # remember the current revision's primary key for later
        old_revision_pk = revision.pk
        # get a list of review tag names for later
        old_review_tags = list(revision.review_tags.names())

        with transaction.atomic():

            # reset primary key
            revision.pk = None

            # add a sensible comment
            revision.comment = ("Revert to revision of %s by %s" %
                                (revision.created, revision.creator))
            if comment:
                revision.comment = u'%s: "%s"' % (revision.comment, comment)
            revision.created = datetime.now()
            revision.creator = user

            if revision.document.original.pk == self.pk:
                revision.based_on_id = old_revision_pk

            revision.save()

            # set review tags
            if old_review_tags:
                revision.review_tags.set(*old_review_tags)

        # populate model instance with fresh data from database
        revision.refresh_from_db()

        # make this new revision the current one for the document
        revision.make_current()
        return revision

    def revise(self, user, data, section_id=None):
        """Given a dict of changes to make, build and save a new Revision to
        revise this document"""
        curr_rev = self.current_revision
        new_rev = Revision(creator=user, document=self, content=self.html)
        for n in ('title', 'slug', 'render_max_age'):
            setattr(new_rev, n, getattr(self, n))
        if curr_rev:
            new_rev.toc_depth = curr_rev.toc_depth
            original_doc = curr_rev.document.original
            if original_doc == self:
                new_rev.based_on = curr_rev
            else:
                new_rev.based_on = original_doc.current_revision

        # Accept optional field edits...

        new_title = data.get('title', False)
        new_rev.title = new_title and new_title or self.title

        new_tags = data.get('tags', False)
        new_rev.tags = (new_tags and new_tags or
                        edit_string_for_tags(self.tags.all()))

        new_review_tags = data.get('review_tags', False)
        if new_review_tags:
            review_tags = new_review_tags
        elif curr_rev:
            review_tags = edit_string_for_tags(curr_rev.review_tags.all())
        else:
            review_tags = ''

        new_rev.summary = data.get('summary', '')

        # To add comment, when Technical/Editorial review completed
        new_rev.comment = data.get('comment', '')

        # Accept HTML edits, optionally by section
        new_html = data.get('content', data.get('html', False))
        if new_html:
            if not section_id:
                new_rev.content = new_html
            else:
                content = parse_content(self.html)
                new_rev.content = (content.replaceSection(section_id, new_html)
                                          .serialize())

        # Finally, commit the revision changes and return the new rev.
        new_rev.save()
        new_rev.review_tags.set(*parse_tags(review_tags))
        return new_rev

    @cached_property
    def last_modified_cache_key(self):
        return DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL % self.natural_cache_key

    def fill_last_modified_cache(self):
        """
        Convert python datetime to Unix epoch seconds. This is more
        easily digested by the cache, and is more compatible with other
        services that might spy on Kuma's cache entries (eg. KumaScript)
        """
        modified_epoch = self.modified.strftime('%s')
        memcache.set(self.last_modified_cache_key, modified_epoch)
        return modified_epoch

    def save(self, *args, **kwargs):

        self.is_template = self.slug.startswith(TEMPLATE_TITLE_PREFIX)
        self.is_redirect = bool(self.get_redirect_url())

        try:
            # Check if the slug would collide with an existing doc
            self._raise_if_collides('slug', SlugCollision)
        except UniqueCollision as err:
            if err.existing.get_redirect_url() is not None:
                # If the existing doc is a redirect, delete it and clobber it.
                err.existing.delete()
            else:
                raise err

        # These are too important to leave to a (possibly omitted) is_valid
        # call:
        self._clean_is_localizable()

        if not self.parent_topic and self.parent:
            # If this is a translation without a topic parent, try to get one.
            self.acquire_translated_topic_parent()

        super(Document, self).save(*args, **kwargs)

        # Delete any cached last-modified timestamp.
        self.fill_last_modified_cache()

    def delete(self, *args, **kwargs):
        if waffle.switch_is_active('wiki_error_on_delete'):
            # bug 863692: Temporary while we investigate disappearing pages.
            raise Exception("Attempt to delete document %s: %s" %
                            (self.id, self.title))
        else:
            if self.is_redirect or 'purge' in kwargs:
                if 'purge' in kwargs:
                    kwargs.pop('purge')
                return super(Document, self).delete(*args, **kwargs)
            signals.pre_delete.send(sender=self.__class__,
                                    instance=self)
            if not self.deleted:
                Document.objects.filter(pk=self.pk).update(deleted=True)
                memcache.delete(self.last_modified_cache_key)

            signals.post_delete.send(sender=self.__class__, instance=self)

    def purge(self):
        if waffle.switch_is_active('wiki_error_on_delete'):
            # bug 863692: Temporary while we investigate disappearing pages.
            raise Exception("Attempt to purge document %s: %s" %
                            (self.id, self.title))
        else:
            if not self.deleted:
                raise Exception("Attempt tp purge non-deleted document %s: %s" %
                                (self.id, self.title))
            self.delete(purge=True)

    def restore(self):
        """
        Restores a logically deleted document by reverting the deleted
        boolean to False. Sends pre_save and post_save Django signals to
        follow ducktyping best practices.
        """
        if not self.deleted:
            raise Exception("Document is not deleted, cannot be restored.")
        signals.pre_save.send(sender=self.__class__, instance=self)
        Document.deleted_objects.filter(pk=self.pk).update(deleted=False)
        signals.post_save.send(sender=self.__class__, instance=self)

    def _post_move_redirects(self, new_slug, user, title):
        """
        Create and return a Document and a Revision to serve as
        redirects once this page has been moved.

        """
        redirect_doc = Document(locale=self.locale,
                                title=self.title,
                                slug=self.slug,
                                is_localizable=False)
        content = REDIRECT_CONTENT % {
            'href': reverse('wiki.document',
                            args=[new_slug],
                            locale=self.locale),
            'title': title,
        }
        redirect_rev = Revision(content=content,
                                is_approved=True,
                                toc_depth=self.current_revision.toc_depth,
                                creator=user)
        return redirect_doc, redirect_rev

    def _moved_revision(self, new_slug, user, title=None):
        """
        Create and return a Revision which is a copy of this
        Document's current Revision, as it will exist at a moved
        location.

        """
        moved_rev = self.current_revision

        # Shortcut trick for getting an object with all the same
        # values, but making Django think it's new.
        moved_rev.id = None

        moved_rev.creator = user
        moved_rev.created = datetime.now()
        moved_rev.slug = new_slug
        if title:
            moved_rev.title = title
        return moved_rev

    def _get_new_parent(self, new_slug):
        """
        Get this moved Document's parent doc if a Document
        exists at the appropriate slug and locale.
        """
        return valid_slug_parent(new_slug, self.locale)

    def _move_conflicts(self, new_slug):
        """
        Given a new slug to be assigned to this document, check
        whether there is an existing, non-redirect, Document at that
        slug in this locale. Any redirect existing there will be
        deleted.

        This is necessary since page moving is a background task, and
        a Document may come into existence at the target slug after
        the move is requested.

        """
        existing = None
        try:
            existing = Document.objects.get(locale=self.locale,
                                            slug=new_slug)
        except Document.DoesNotExist:
            pass

        if existing is not None:
            if existing.is_redirect:
                existing.delete()
            else:
                raise Exception("Requested move would overwrite a non-redirect page.")

    def _tree_conflicts(self, new_slug):
        """
        Given a new slug to be assigned to this document, return a
        list of documents (if any) which would be overwritten by
        moving this document or any of its children in that fashion.
        """
        conflicts = []
        try:
            existing = Document.objects.get(locale=self.locale, slug=new_slug)
            if not existing.is_redirect:
                conflicts.append(existing)
        except Document.DoesNotExist:
            pass
        for child in self.get_descendants():
            child_title = child.slug.split('/')[-1]
            try:
                slug = '/'.join([new_slug, child_title])
                existing = Document.objects.get(locale=self.locale, slug=slug)
                if not existing.get_redirect_url():
                    conflicts.append(existing)
            except Document.DoesNotExist:
                pass
        return conflicts

    def _move_tree(self, new_slug, user=None, title=None):
        """
        Move this page and all its children.
        """
        # Page move is a 10-step process.
        #
        # Step 1: Sanity check. Has a page been created at this slug
        # since the move was requested? If not, OK to go ahead and
        # change our slug.
        self._move_conflicts(new_slug)

        if user is None:
            user = self.current_revision.creator
        if title is None:
            title = self.title

        # Step 2: stash our current review tags, since we want to
        # preserve them.
        review_tags = list(self.current_revision.review_tags.names())

        # Step 3: Create (but don't yet save) a Document and Revision
        # to leave behind as a redirect from old location to new.
        redirect_doc, redirect_rev = self._post_move_redirects(new_slug,
                                                               user,
                                                               title)

        # Step 4: Update our breadcrumbs.
        new_parent = self._get_new_parent(new_slug)

        # If we found a Document at what will be our parent slug, set
        # it as our parent_topic. If we didn't find one, then we no
        # longer have a parent_topic (since our original parent_topic
        # would already have moved if it were going to).
        self.parent_topic = new_parent

        # Step 5: Save this Document.
        self.slug = new_slug
        self.save()

        # Step 6: Create (but don't yet save) a copy of our current
        # revision, but with the new slug and title (if title is
        # changing too).
        moved_rev = self._moved_revision(new_slug, user, title)

        # Step 7: Save the Revision that actually moves us.
        moved_rev.save(force_insert=True)

        # Step 8: Save the review tags.
        moved_rev.review_tags.set(*review_tags)

        # Step 9: Save the redirect.
        redirect_doc.save()
        redirect_rev.document = redirect_doc
        redirect_rev.save()

        # Finally, step 10: recurse through all of our children.
        for child in self.children.filter(locale=self.locale):
            # Save the original slug and locale so we can use them in
            # the error message if something goes wrong.
            old_child_slug, old_child_locale = child.slug, child.locale

            child_title = child.slug.split('/')[-1]
            try:
                child._move_tree('/'.join([new_slug, child_title]), user)
            except PageMoveError:
                # A child move already caught this and created the
                # correct exception + error message, so just propagate
                # it up.
                raise
            except Exception as e:
                # One of the immediate children of this page failed to
                # move.
                exc_class, exc_message, exc_tb = sys.exc_info()
                message = """
Failure occurred while attempting to move document
with id %(doc_id)s.

That document can be viewed at:

https://developer.mozilla.org/%(locale)s/docs/%(slug)s

The exception raised was:

Exception type: %(exc_class)s

Exception message: %(exc_message)s

Full traceback:

%(traceback)s
                """ % {'doc_id': child.id,
                       'locale': old_child_locale,
                       'slug': old_child_slug,
                       'exc_class': exc_class,
                       'exc_message': exc_message,
                       'traceback': traceback.format_exc(e)}
                raise PageMoveError(message)

    def repair_breadcrumbs(self):
        """
        Temporary method while we work out the real issue behind
        translation/breadcrumb mismatches (bug 900961).

        Basically just walks up the tree of topical parents, calling
        acquire_translated_topic_parent() for as long as there's a
        language mismatch.
        """
        if (not self.parent_topic or
                self.parent_topic.locale != self.locale):
            self.acquire_translated_topic_parent()
        if self.parent_topic:
            self.parent_topic.repair_breadcrumbs()

    def acquire_translated_topic_parent(self):
        """
        This normalizes topic breadcrumb paths between locales.

        Attempt to acquire a topic parent from a translation of our translation
        parent's topic parent, auto-creating a stub document if necessary.
        """
        if not self.parent:
            # Bail, if this is not in fact a translation.
            return
        parent_topic = self.parent.parent_topic
        if not parent_topic:
            # Bail, if the translation parent has no topic parent
            return
        try:
            # Look for an existing translation of the topic parent
            new_parent = parent_topic.translations.get(locale=self.locale)
        except Document.DoesNotExist:
            try:
                # No luck. As a longshot, let's try looking for the same slug.
                new_parent = Document.objects.get(locale=self.locale,
                                                  slug=parent_topic.slug)
                if not new_parent.parent:
                    # HACK: This same-slug/different-locale doc should probably
                    # be considered a translation. Let's correct that on the
                    # spot.
                    new_parent.parent = parent_topic
                    new_parent.save()
            except Document.DoesNotExist:
                # Finally, let's create a translated stub for a topic parent
                new_parent = Document.objects.get(pk=parent_topic.pk)
                new_parent.pk = None
                new_parent.current_revision = None
                new_parent.parent_topic = None
                new_parent.parent = parent_topic
                new_parent.locale = self.locale
                new_parent.save()

                if parent_topic.current_revision:
                    # Don't forget to clone a current revision
                    new_rev = Revision.objects.get(pk=parent_topic.current_revision.pk)
                    new_rev.pk = None
                    new_rev.document = new_parent
                    # HACK: Let's auto-add tags that flag this as a topic stub
                    stub_tags = '"TopicStub","NeedsTranslation"'
                    stub_l10n_tags = ['inprogress']
                    if new_rev.tags:
                        new_rev.tags = '%s,%s' % (new_rev.tags, stub_tags)
                    else:
                        new_rev.tags = stub_tags
                    new_rev.save()
                    new_rev.localization_tags.add(*stub_l10n_tags)

        # Finally, assign the new default parent topic
        self.parent_topic = new_parent
        self.save()

    @property
    def content_parsed(self):
        if not self.current_revision:
            return None
        return self.current_revision.content_parsed

    def populate_attachments(self):
        """
        File attachments are stored at the DB level and synced here
        with the document's HTML content.

        We find them by regex-searching over the HTML for URLs that match the
        file URL patterns.
        """
        mt_files = DEKI_FILE_URL.findall(self.html)
        kuma_files = KUMA_FILE_URL.findall(self.html)
        params = None

        if mt_files:
            # We have at least some MindTouch files.
            params = models.Q(mindtouch_attachment_id__in=mt_files)
            if kuma_files:
                # We also have some kuma files. Use an OR query.
                params = params | models.Q(id__in=kuma_files)
        if kuma_files and not params:
            # We have only kuma files.
            params = models.Q(id__in=kuma_files)

        Attachment = apps.get_model('attachments', 'Attachment')
        if params:
            found_attachments = Attachment.objects.filter(params)
        else:
            # If no files found, return an empty Attachment queryset.
            found_attachments = Attachment.objects.none()

        # Delete all document-attachments-relations for attachments that
        # weren't originally uploaded for the document to populate the list
        # again below
        self.attached_files.filter(is_original=False).delete()

        # Reset the linked status for all attachments that are left
        self.attached_files.all().update(is_linked=False)

        # Go through the attachments discovered in the HTML and
        # create linked attachments
        """
        three options of state:

        - linked in the document, but not originally uploaded
        - linked in the document and originally uploaded
        - not linked in the document, but originally uploaded
        """
        populated = []
        for attachment in (found_attachments.only('pk', 'current_revision')
                                            .iterator()):
            revision = attachment.current_revision
            relation, created = self.files.through.objects.update_or_create(
                file_id=attachment.pk,
                document_id=self.pk,
                defaults={
                    'attached_by': revision.creator,
                    'name': revision.filename,
                    'is_linked': True,
                },
            )
            populated.append((relation, created))
        return populated

    @property
    def show_toc(self):
        return self.current_revision and self.current_revision.toc_depth

    @cached_property
    def language(self):
        return get_language_mapping()[self.locale.lower()]

    def get_absolute_url(self, endpoint='wiki.document'):
        """
        Build the absolute URL to this document from its full path
        """
        return reverse(endpoint, locale=self.locale, args=[self.slug])

    def get_edit_url(self):
        return self.get_absolute_url(endpoint='wiki.edit')

    def get_redirect_url(self):
        """
        If I am a redirect, return the absolute URL to which I redirect.

        Otherwise, return None.
        """
        # If a document starts with REDIRECT_HTML and contains any <a> tags
        # with hrefs, return the href of the first one. This trick saves us
        # from having to parse the HTML every time.
        if REDIRECT_HTML in self.html:
            anchors = PyQuery(self.html)('a[href].redirect')
            if anchors:
                url = anchors[0].get('href')
                # allow explicit domain and *not* '//'
                # i.e allow "https://developer...." and "/en-US/docs/blah"
                if len(url) > 1:
                    if url.startswith(settings.SITE_URL):
                        return url
                    elif url[0] == '/' and url[1] != '/':
                        return url
                elif len(url) == 1 and url[0] == '/':
                    return url

    def get_topic_parents(self):
        """Build a list of parent topics from self to root"""
        curr, parents = self, []
        while curr.parent_topic:
            curr = curr.parent_topic
            parents.append(curr)
        return parents

    def allows_revision_by(self, user):
        """
        Return whether `user` is allowed to create new revisions of me.

        The motivation behind this method is that templates and other types of
        docs may have different permissions.
        """
        if (self.slug.startswith(TEMPLATE_TITLE_PREFIX) and
                not user.has_perm('wiki.change_template_document')):
            return False
        return True

    def allows_editing_by(self, user):
        """
        Return whether `user` is allowed to edit document-level metadata.

        If the Document doesn't have a current_revision (nothing approved) then
        all the Document fields are still editable. Once there is an approved
        Revision, the Document fields can only be edited by privileged users.
        """
        if (self.slug.startswith(TEMPLATE_TITLE_PREFIX) and
                not user.has_perm('wiki.change_template_document')):
            return False
        return (not self.current_revision or
                user.has_perm('wiki.change_document'))

    def translated_to(self, locale):
        """
        Return the translation of me to the given locale.

        If there is no such Document, return None.
        """
        if self.locale != settings.WIKI_DEFAULT_LANGUAGE:
            raise NotImplementedError('translated_to() is implemented only on'
                                      'Documents in the default language so'
                                      'far.')
        try:
            return Document.objects.get(locale=locale, parent=self)
        except Document.DoesNotExist:
            return None

    @property
    def original(self):
        """
        Return the document I was translated from or, if none, myself.
        """
        return self.parent or self

    @cached_property
    def other_translations(self):
        """
        Return a list of Documents - other translations of this Document
        """
        if self.parent is None:
            return self.translations.all().order_by('locale')
        else:
            translations = (self.parent.translations.all()
                                .exclude(id=self.id)
                                .order_by('locale'))
            pks = list(translations.values_list('pk', flat=True))
            return Document.objects.filter(pk__in=[self.parent.pk] + pks)

    @property
    def parents(self):
        """
        Return the list of topical parent documents above this one,
        or an empty list if none exist.
        """
        if self.parent_topic is None:
            return []
        current_parent = self.parent_topic
        parents = [current_parent]
        while current_parent.parent_topic is not None:
            parents.insert(0, current_parent.parent_topic)
            current_parent = current_parent.parent_topic
        return parents

    def is_child_of(self, other):
        """
        Circular dependency detection -- if someone tries to set
        this as a parent of a document it's a child of, they're gonna
        have a bad time.
        """
        return other.id in (d.id for d in self.parents)

    # This is a method, not a property, because it can do a lot of DB
    # queries and so should look scarier. It's not just named
    # 'children' because that's taken already by the reverse relation
    # on parent_topic.
    def get_descendants(self, limit=None, levels=0):
        """
        Return a list of all documents which are children
        (grandchildren, great-grandchildren, etc.) of this one.
        """
        results = []

        if (limit is None or levels < limit) and self.children.exists():
            for child in self.children.all().filter(locale=self.locale):
                results.append(child)
                [results.append(grandchild)
                 for grandchild in child.get_descendants(limit, levels + 1)]
        return results

    def is_watched_by(self, user):
        """
        Return whether `user` is notified of edits to me.
        """
        from .events import EditDocumentEvent
        return EditDocumentEvent.is_notifying(user, self)

    def tree_is_watched_by(self, user):
        """Return whether `user` is notified of edits to me AND sub-pages."""
        from .events import EditDocumentInTreeEvent
        return EditDocumentInTreeEvent.is_notifying(user, self)

    def parent_trees_watched_by(self, user):
        """
        Return any and all of this document's parents that are watched by the
        given user.
        """
        return [doc for doc in self.parents if doc.tree_is_watched_by(user)]

    @cached_property
    def contributors(self):
        return DocumentContributorsJob().get(self.pk)

    @cached_property
    def zone_stack(self):
        return DocumentZoneStackJob().get(self.pk)

    def get_full_url(self):
        return absolutify(self.get_absolute_url())


class DocumentDeletionLog(models.Model):
    """
    Log of who deleted a Document, when, and why.
    """
    # We store the locale/slug because it's unique, and also because a
    # ForeignKey would delete this log when the Document gets purged.
    locale = models.CharField(
        max_length=7,
        choices=settings.LANGUAGES,
        default=settings.WIKI_DEFAULT_LANGUAGE,
        db_index=True,
    )

    slug = models.CharField(max_length=255, db_index=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    timestamp = models.DateTimeField(auto_now=True)
    reason = models.TextField()

    def __unicode__(self):
        return "/%(locale)s/%(slug)s deleted by %(user)s" % {
            'locale': self.locale,
            'slug': self.slug,
            'user': self.user
        }


class DocumentZone(models.Model):
    """
    Model object declaring a content zone root at a given Document, provides
    attributes inherited by the topic hierarchy beneath it.
    """
    document = models.OneToOneField(Document, related_name='zone')
    styles = models.TextField(null=True, blank=True)
    url_root = models.CharField(
        max_length=255, null=True, blank=True, db_index=True,
        help_text="alternative URL path root for documents under this zone")

    def __unicode__(self):
        return u'DocumentZone %s (%s)' % (self.document.get_absolute_url(),
                                          self.document.title)


class ReviewTag(TagBase):
    """A tag indicating review status, mainly for revisions"""
    class Meta:
        verbose_name = _('Review Tag')
        verbose_name_plural = _('Review Tags')


class LocalizationTag(TagBase):
    """A tag indicating localization status, mainly for revisions"""
    class Meta:
        verbose_name = _('Localization Tag')
        verbose_name_plural = _('Localization Tags')


class ReviewTaggedRevision(ItemBase):
    """Through model, just for review tags on revisions"""
    content_object = models.ForeignKey('Revision')
    tag = models.ForeignKey(ReviewTag, related_name="%(app_label)s_%(class)s_items")

    @classmethod
    def tags_for(cls, *args, **kwargs):
        return tags_for(cls, *args, **kwargs)


class LocalizationTaggedRevision(ItemBase):
    """Through model, just for localization tags on revisions"""
    content_object = models.ForeignKey('Revision')
    tag = models.ForeignKey(LocalizationTag, related_name="%(app_label)s_%(class)s_items")

    @classmethod
    def tags_for(cls, *args, **kwargs):
        return tags_for(cls, *args, **kwargs)


class Revision(models.Model):
    """A revision of a localized knowledgebase document"""
    # Depth of table-of-contents in document display.
    TOC_DEPTH_NONE = 0
    TOC_DEPTH_ALL = 1
    TOC_DEPTH_H2 = 2
    TOC_DEPTH_H3 = 3
    TOC_DEPTH_H4 = 4

    TOC_DEPTH_CHOICES = (
        (TOC_DEPTH_NONE, _(u'No table of contents')),
        (TOC_DEPTH_ALL, _(u'All levels')),
        (TOC_DEPTH_H2, _(u'H2 and higher')),
        (TOC_DEPTH_H3, _(u'H3 and higher')),
        (TOC_DEPTH_H4, _('H4 and higher')),
    )

    document = models.ForeignKey(Document, related_name='revisions')

    # Title and slug in document are primary, but they're kept here for
    # revision history.
    title = models.CharField(max_length=255, null=True, db_index=True)
    slug = models.CharField(max_length=255, null=True, db_index=True)

    summary = models.TextField()  # wiki markup
    content = models.TextField()  # wiki markup
    tidied_content = models.TextField(blank=True)  # wiki markup tidied up

    # Keywords are used mostly to affect search rankings. Moderators may not
    # have the language expertise to translate keywords, so we put them in the
    # Revision so the translators can handle them:
    keywords = models.CharField(max_length=255, blank=True)

    # Tags are stored in a Revision as a plain CharField, because Revisions are
    # not indexed by tags. This data is retained for history tracking.
    tags = models.CharField(max_length=255, blank=True)

    # Tags are (ab)used as status flags and for searches, but the through model
    # should constrain things from getting expensive.
    review_tags = TaggableManager(through=ReviewTaggedRevision)

    localization_tags = TaggableManager(through=LocalizationTaggedRevision)

    toc_depth = models.IntegerField(choices=TOC_DEPTH_CHOICES,
                                    default=TOC_DEPTH_ALL)

    # Maximum age (in seconds) before this document needs re-rendering
    render_max_age = models.IntegerField(blank=True, null=True)

    created = models.DateTimeField(default=datetime.now, db_index=True)
    comment = models.CharField(max_length=255)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name='created_revisions')
    is_approved = models.BooleanField(default=True, db_index=True)

    # The default locale's rev that was current when the Edit button was hit to
    # create this revision. Used to determine whether localizations are out of
    # date.
    based_on = models.ForeignKey('self', null=True, blank=True)
    # TODO: limit_choices_to={'document__locale':
    # settings.WIKI_DEFAULT_LANGUAGE} is a start but not sufficient.

    is_mindtouch_migration = models.BooleanField(default=False, db_index=True,
                                                 help_text="Did this revision come from MindTouch?")

    objects = TransformManager()

    def get_absolute_url(self):
        """Build the absolute URL to this revision"""
        return reverse('wiki.revision',
                       locale=self.document.locale,
                       args=[self.document.slug, self.pk])

    def _based_on_is_clean(self):
        """Return a tuple: (the correct value of based_on, whether the old
        value was correct).

        based_on must be an approved revision of the English version of the
        document if there are any such revisions, any revision if no
        approved revision exists, and None otherwise. If based_on is not
        already set when this is called, the return value defaults to the
        current_revision of the English document.

        """
        # TODO(james): This could probably be simplified down to "if
        # based_on is set, it must be a revision of the original document."
        original = self.document.original
        base = original.current_or_latest_revision()
        has_approved = original.revisions.filter(is_approved=True).exists()
        if (original.current_revision or not has_approved):
            if (self.based_on and self.based_on.document != original):
                # based_on is set and points to the wrong doc.
                return base, False
            # Else based_on is valid; leave it alone.
        elif self.based_on:
            return None, False
        return self.based_on, True

    def clean(self):
        """Ensure based_on is valid."""
        # All of the cleaning herein should be unnecessary unless the user
        # messes with hidden form data.
        try:
            self.document and self.document.original
        except Document.DoesNotExist:
            # For clean()ing forms that don't have a document instance behind
            # them yet
            self.based_on = None
        else:
            based_on, is_clean = self._based_on_is_clean()
            if not is_clean:
                if self.document.parent:
                    # Restoring translation source, so base on current_revision
                    self.based_on = self.document.parent.current_revision
                else:
                    old = self.based_on
                    self.based_on = based_on  # Guess a correct value.
                    locale = settings.LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native
                    error = ugettext(
                        'A revision must be based on a revision of the '
                        '%(locale)s document. Revision ID %(id)s does '
                        'not fit those criteria.')
                    raise ValidationError(error %
                                          {'locale': locale, 'id': old.id})

    def save(self, *args, **kwargs):
        _, is_clean = self._based_on_is_clean()
        if not is_clean:  # No more Mister Nice Guy
            # TODO(erik): This error message ignores non-translations.
            raise ProgrammingError('Revision.based_on must be None or refer '
                                   'to a revision of the default-'
                                   'language document. It was %s' %
                                   self.based_on)

        if not self.title:
            self.title = self.document.title
        if not self.slug:
            self.slug = self.document.slug

        super(Revision, self).save(*args, **kwargs)

        # When a revision is approved, update document metadata and re-cache
        # the document's html content
        if self.is_approved:
            self.make_current()

    def make_current(self):
        """
        Make this revision the current one for the document
        """
        self.document.title = self.title
        self.document.slug = self.slug
        self.document.html = self.content_cleaned
        self.document.render_max_age = self.render_max_age
        self.document.current_revision = self

        # Since Revision stores tags as a string, we need to parse them first
        # before setting on the Document.
        self.document.tags.set(*parse_tags(self.tags))

        self.document.save()

        # Re-create all document-attachment relations since they are based
        # on the actual HTML content
        self.document.populate_attachments()

    def __unicode__(self):
        return u'[%s] %s #%s' % (self.document.locale,
                                 self.document.title,
                                 self.id)

    def get_section_content(self, section_id):
        """Convenience method to extract the content for a single section"""
        return self.document.extract.section(self.content, section_id)

    def get_tidied_content(self, allow_none=False):
        """
        Return the revision content parsed and cleaned by tidy.

        First, check in denormalized db field. If it's not available, schedule
        an asynchronous task to store it.

        allow_none -- To prevent CPU-hogging calls, return None instead of
                      calling tidy_content in-process.
        """
        # we may be lucky and have the tidied content already denormalized
        # in the database, if so return it
        if self.tidied_content:
            tidied_content = self.tidied_content
        else:
            if allow_none:
                if self.pk:
                    from .tasks import tidy_revision_content
                    tidy_revision_content.delay(self.pk, refresh=False)
                tidied_content = None
            else:
                tidied_content, errors = tidy_content(self.content)
                if self.pk:
                    Revision.objects.filter(pk=self.pk).update(
                        tidied_content=tidied_content)
        self.tidied_content = tidied_content or ''
        return tidied_content

    @property
    def content_cleaned(self):
        if self.document.is_template:
            return self.content
        else:
            return Document.objects.clean_content(self.content)

    @cached_property
    def previous(self):
        return self.get_previous()

    def get_previous(self):
        """
        Returns the previous approved revision or None.
        """
        try:
            return self.document.revisions.filter(
                is_approved=True,
                created__lt=self.created,
            ).order_by('-created')[0]
        except IndexError:
            return None

    @cached_property
    def needs_editorial_review(self):
        return self.review_tags.filter(name='editorial').exists()

    @cached_property
    def needs_technical_review(self):
        return self.review_tags.filter(name='technical').exists()

    @cached_property
    def localization_in_progress(self):
        return self.localization_tags.filter(name='inprogress').exists()

    @property
    def translation_age(self):
        return abs((datetime.now() - self.created).days)


class RevisionIP(models.Model):
    """
    IP Address for a Revision including User-Agent string and Referrer URL.
    """
    revision = models.ForeignKey(
        Revision
    )
    ip = models.CharField(
        _('IP address'),
        max_length=40,
        editable=False,
        db_index=True,
        blank=True,
        null=True,
    )
    user_agent = models.TextField(
        _('User-Agent'),
        editable=False,
        blank=True,
    )
    referrer = models.TextField(
        _('HTTP Referrer'),
        editable=False,
        blank=True,
    )
    data = models.TextField(
        editable=False,
        blank=True,
        null=True,
        verbose_name=_('Data submitted to Akismet')
    )
    objects = RevisionIPManager()

    def __unicode__(self):
        return '%s (revision %d)' % (self.ip or 'No IP', self.revision.id)


class RevisionAkismetSubmission(AkismetSubmission):
    """
    The Akismet submission per wiki document revision.

    Stores only a reference to the submitted revision.
    """
    revision = models.ForeignKey(
        Revision,
        related_name='akismet_submissions',
        null=True,
        blank=True,
        verbose_name=_('Revision'),
        # don't delete the akismet submission but set the revision to null
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _('Akismet submission')
        verbose_name_plural = _('Akismet submissions')

    def __unicode__(self):
        if self.revision:
            return (
                u'%(type)s submission by %(sender)s (Revision %(revision_id)d)' % {
                    'type': self.get_type_display(),
                    'sender': self.sender,
                    'revision_id': self.revision.id,
                }
            )
        else:
            return (
                u'%(type)s submission by %(sender)s (no revision)' % {
                    'type': self.get_type_display(),
                    'sender': self.sender,
                }
            )


class EditorToolbar(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name='created_toolbars')
    default = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    code = models.TextField(max_length=2000)

    def __unicode__(self):
        return self.name


class DocumentSpamAttempt(SpamAttempt):
    """
    The wiki document specific spam attempt.

    Stores title, slug and locale of the documet revision to be able
    to see where it happens. Stores data sent to Akismet so that staff can
    review Akismet's spam detection for false positives.
    """
    title = models.CharField(
        verbose_name=_('Title'),
        max_length=255,
    )
    slug = models.CharField(
        verbose_name=_('Slug'),
        max_length=255,
    )
    document = models.ForeignKey(
        Document,
        related_name='spam_attempts',
        null=True,
        blank=True,
        verbose_name=_('Document (optional)'),
        on_delete=models.SET_NULL,
    )
    data = models.TextField(
        editable=False,
        blank=True,
        null=True,
        verbose_name=_('Data submitted to Akismet')
    )
    reviewed = models.DateTimeField(
        _('reviewed'),
        blank=True,
        null=True,
    )

    NEEDS_REVIEW = 0
    HAM = 1
    SPAM = 2
    REVIEW_UNAVAILABLE = 3
    AKISMET_ERROR = 4
    REVIEW_CHOICES = (
        (NEEDS_REVIEW, _('Needs Review')),
        (HAM, _('Ham / False Positive')),
        (SPAM, _('Confirmed as Spam')),
        (REVIEW_UNAVAILABLE, _('Review Unavailable')),
        (AKISMET_ERROR, _('Akismet Error')),
    )
    review = models.IntegerField(
        choices=REVIEW_CHOICES,
        default=NEEDS_REVIEW,
        verbose_name=_("Review of Akismet's classification as spam"),
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='documentspam_reviewed',
        blank=True,
        null=True,
        verbose_name=_('Staff reviewer'),
    )

    def __unicode__(self):
        return u'%s (%s)' % (self.slug, self.title)
