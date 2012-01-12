from collections import namedtuple
from datetime import datetime
from itertools import chain
from urlparse import urlparse

from pyquery import PyQuery
from tower import ugettext_lazy as _lazy, ugettext as _
import bleach

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.db import models
from django.http import Http404

from south.modelsinspector import add_introspection_rules

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter

from notifications.models import NotificationsMixin
from sumo import ProgrammingError
from sumo_locales import LOCALES
from sumo.models import ManagerBase, ModelBase, LocaleField
from sumo.urlresolvers import reverse, split_path
from tags.models import BigVocabTaggableMixin
from wiki import TEMPLATE_TITLE_PREFIX
import wiki.content

import caching.base

from taggit.models import ItemBase, TaggedItemBase, TaggedItem, TagBase
from taggit.managers import TaggableManager


ALLOWED_TAGS = bleach.ALLOWED_TAGS + [
    'div', 'span', 'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre', 'code',
    'dl', 'dt', 'dd',
    'img', 
    'input',
    'table', 'tbody', 'thead', 'tr', 'th', 'td',
    'section', 'header', 'footer', 'nav', 'article', 'aside', 'figure',
    'dialog', 'hgroup', 'mark', 'time', 'meter', 'command', 'output',
    'progress', 'audio', 'video', 'details', 'datagrid', 'datalist', 'table',
    'address'
]
ALLOWED_ATTRIBUTES = bleach.ALLOWED_ATTRIBUTES
ALLOWED_ATTRIBUTES['span'] = ['style', ]
ALLOWED_ATTRIBUTES['img'] = ['src', 'id', 'align', 'alt', 'class', 'is', 'title', 'style']
ALLOWED_ATTRIBUTES['a'] = ['id', 'class', 'href', 'title', ]
ALLOWED_ATTRIBUTES.update(dict((x, ['id', ]) for x in (
    'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre', 'code', 'dl', 'dt', 'dd',
    'section', 'header', 'footer', 'nav', 'article', 'aside', 'figure',
    'dialog', 'hgroup', 'mark', 'time', 'meter', 'command', 'output',
    'progress', 'audio', 'video', 'details', 'datagrid', 'datalist', 'table',
    'address'
)))

# Disruptiveness of edits to translated versions. Numerical magnitude indicate
# the relative severity.
TYPO_SIGNIFICANCE = 10
MEDIUM_SIGNIFICANCE = 20
MAJOR_SIGNIFICANCE = 30
SIGNIFICANCES = (
    (TYPO_SIGNIFICANCE,
     _lazy(u'Minor details like punctuation and spelling errors')),
    (MEDIUM_SIGNIFICANCE,
     _lazy(u"Content changes that don't require immediate translation")),
    (MAJOR_SIGNIFICANCE,
     _lazy(u'Major content changes that will make older translations '
           'inaccurate')),
)

CATEGORIES = (
    (00, _lazy(u'Uncategorized')),
    (10, _lazy(u'Reference')),
)

# FF versions used to filter article searches, power {for} tags, etc.:
#
# Iterables of (ID, name, abbreviation for {for} tags, max version this version
# group encompasses) grouped into optgroups. To add the ability to sniff a new
# version of an existing browser (assuming it doesn't change the user agent
# string too radically), you should need only to add a line here; no JS
# required. Just be wary of inexact floating point comparisons when setting
# max_version, which should be read as "From the next smaller max_version up to
# but not including version x.y".
VersionMetadata = namedtuple('VersionMetadata',
                             'id, name, long, slug, max_version, show_in_ui')
GROUPED_FIREFOX_VERSIONS = (
    ((_lazy(u'Desktop:'), 'desktop'), (
        # The first option is the default for {for} display. This should be the
        # newest version.
        VersionMetadata(2, _lazy(u'Firefox 3.5-3.6'),
                        _lazy(u'Firefox 3.5-3.6'), 'fx35', 3.9999, True),
        VersionMetadata(1, _lazy(u'Firefox 4'),
                        _lazy(u'Firefox 4'), 'fx4', 4.9999, True),
        VersionMetadata(3, _lazy(u'Firefox 3.0'),
                        _lazy(u'Firefox 3.0'), 'fx3', 3.4999, False))),
    ((_lazy(u'Mobile:'), 'mobile'), (
        VersionMetadata(4, _lazy(u'Firefox 4'),
                        _lazy(u'Firefox 4 for Mobile'), 'm4', 4.9999, True),)))

# Flattened:  # TODO: perhaps use optgroups everywhere instead
FIREFOX_VERSIONS = tuple(chain(*[options for label, options in
                                 GROUPED_FIREFOX_VERSIONS]))

# OSes used to filter articles and declare {for} sections:
OsMetaData = namedtuple('OsMetaData', 'id, name, slug')
GROUPED_OPERATING_SYSTEMS = (
    ((_lazy(u'Desktop OS:'), 'desktop'), (
        OsMetaData(1, _lazy(u'Windows'), 'win'),
        OsMetaData(2, _lazy(u'Mac OS X'), 'mac'),
        OsMetaData(3, _lazy(u'Linux'), 'linux'))),
    ((_lazy(u'Mobile OS:'), 'mobile'), (
        OsMetaData(5, _lazy(u'Android'), 'android'),
        OsMetaData(4, _lazy(u'Maemo'), 'maemo'))))

# Flattened
OPERATING_SYSTEMS = tuple(chain(*[options for label, options in
                                  GROUPED_OPERATING_SYSTEMS]))


# how a redirect looks as rendered HTML
REDIRECT_HTML = 'REDIRECT <a class="redirect"'
REDIRECT_CONTENT = 'REDIRECT <a class="redirect" href="%(href)s">%(title)s</a>'
REDIRECT_TITLE = _lazy(u'%(old)s Redirect %(number)i')
REDIRECT_SLUG = _lazy(u'%(old)s-redirect-%(number)i')

# TODO: Put this under the control of Constance / Waffle?
# Flags used to signify revisions in need of review
REVIEW_FLAG_TAGS = (
    ('technical', _('Technical - code samples, APIs, or technologies')),
    ('editorial', _('Editorial - prose, grammar, or content')),
)

# TODO: This is info derived from urls.py, but unsure how to DRY it
RESERVED_SLUGS = (
    'ckeditor_config.js$',
    'watch-ready-for-review$',
    'unwatch-ready-for-review$',
    'watch-approved$',
    'unwatch-approved$',
    '.json$',
    'new$',
    'all$',
    'preview-wiki-content$',
    'category/\d+$',
    'needs-review/?[^/]+$',
    'needs-review/?',
    'feeds/[^/]+/all/?',
    'feeds/[^/]+/needs-review/[^/]+$',
    'feeds/[^/]+/needs-review/?',
    'tag/[^/]+'
)


class UniqueCollision(Exception):
    """An attempt to create two pages with the same unique metadata"""
    def __init__(self, existing):
        self.existing = existing


class TitleCollision(UniqueCollision):
    """An attempt to create two pages of the same title in one locale"""


class SlugCollision(UniqueCollision):
    """An attempt to create two pages of the same slug in one locale"""


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
                               if self.parent
                           else getattr(self, direct_attr))
    setter = lambda self, val: (setattr(self.parent, parent_attr,
                                        val) if self.parent else
                                setattr(self, direct_attr, val))
    return property(getter, setter)


class DocumentManager(ManagerBase):
    """Manager for Documents, assists for queries"""

    def filter_for_list(self, locale=None, category=None, tag=None,
                        tag_name=None):
        docs = self.order_by('title')
        if locale:
            docs = docs.filter(locale=locale)
        if category:
            docs = docs.filter(category=category)
        if tag:
            docs = docs.filter(tags__in=[tag.name])
        if tag_name:
            docs = docs.filter(tags__name=tag_name)
        # Leave out the html, since that leads to huge cache objects and we
        # never use the content in lists.
        docs = docs.defer('html')
        return docs

    def filter_for_review(self, tag=None, tag_name=None):
        """Filter for documents with current revision flagged for review"""
        bq = 'current_revision__review_tags__%s'
        if tag_name:
            q = {bq % 'name': tag_name}
        elif tag:
            q = {bq % 'in': [tag]}
        else:
            q = {bq % 'name__isnull': False}
        return self.filter(**q).distinct()


class Document(NotificationsMixin, ModelBase, BigVocabTaggableMixin):
    """A localized knowledgebase document, not revision-specific."""
    objects = DocumentManager()

    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # Is this document a template or not?
    is_template = models.BooleanField(default=False, editable=False,
                                      db_index=True)
    # Is this document localizable or not?
    is_localizable = models.BooleanField(default=True, db_index=True)

    # TODO: validate (against settings.SUMO_LANGUAGES?)
    locale = LocaleField(default=settings.WIKI_DEFAULT_LANGUAGE, db_index=True)

    # Latest approved revision. L10n dashboard depends on this being so (rather
    # than being able to set it to earlier approved revisions). (Remove "+" to
    # enable reverse link.)
    current_revision = models.ForeignKey('Revision', null=True,
                                         related_name='current_for+')

    # The Document I was translated from. NULL iff this doc is in the default
    # locale or it is nonlocalizable. TODO: validate against
    # settings.WIKI_DEFAULT_LANGUAGE.
    parent = models.ForeignKey('self', related_name='translations',
                               null=True, blank=True)

    # Related documents, based on tags in common.
    # The RelatedDocument table is populated by
    # wiki.cron.calculate_related_documents.
    related_documents = models.ManyToManyField('self',
                                               through='RelatedDocument',
                                               symmetrical=False)

    # Cached HTML rendering of approved revision's wiki markup:
    html = models.TextField(editable=False)

    # A document's category much always be that of its parent. If it has no
    # parent, it can do what it wants. This invariant is enforced in save().
    category = models.IntegerField(choices=CATEGORIES, db_index=True)

    # HACK: Migration bookkeeping - index by the old_id of MindTouch revisions
    # so that migrations can be idempotent.
    mindtouch_page_id = models.IntegerField(
            help_text="ID for migrated MindTouch page",
            null=True, db_index=True)

    # Last modified time for the document. Should be equal-to or greater than
    # the current revision's created field
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    # firefox_versions,
    # operating_systems:
    #    defined in the respective classes below. Use them as in
    #    test_firefox_versions.

    # TODO: Rethink indexes once controller code is near complete. Depending on
    # how MySQL uses indexes, we probably don't need individual indexes on
    # title and locale as well as a combined (title, locale) one.
    class Meta(object):
        unique_together = (('parent', 'locale'), ('title', 'locale'),
                           ('slug', 'locale'))

    def _existing(self, attr, value):
        """Return an existing doc (if any) in this locale whose `attr` attr is
        equal to mine."""
        return Document.uncached.filter(locale=self.locale,
                                        **{attr: value})

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
        self._clean_category()

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
        if self.parent and not self.parent.is_localizable:
            raise ValidationError('"%s": parent "%s" is not localizable.' % (
                                  unicode(self), unicode(self.parent)))

        # Can't make not localizable if it has translations
        # This only applies to documents that already exist, hence self.pk
        # TODO: Use uncached manager here, if we notice problems
        if self.pk and not self.is_localizable and self.translations.exists():
            raise ValidationError('"%s": document has %s translations but is '
                                  'not localizable.' % (
                                  unicode(self), self.translations.count()))

    def _clean_category(self):
        """Make sure a doc's category is the same as its parent's."""
        parent = self.parent
        if parent:
            self.category = parent.category
        elif self.category not in (id for id, name in CATEGORIES):
            # All we really need to do here is make sure category != '' (which
            # is what it is when it's missing from the DocumentForm). The extra
            # validation is just a nicety.
            raise ValidationError(_('Please choose a category.'))
        else:  # An article cannot have both a parent and children.
            # Make my children the same as me:
            if self.id:
                self.translations.all().update(category=self.category)

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

    def save(self, *args, **kwargs):
        self.is_template = self.title.startswith(TEMPLATE_TITLE_PREFIX)

        try:
            # Check if the slug or title would collide with an existing doc
            self._raise_if_collides('slug', SlugCollision)
            self._raise_if_collides('title', TitleCollision)
        except UniqueCollision, e:
            if e.existing.redirect_url() is not None:
                # If the existing doc is a redirect, delete it and clobber it.
                e.existing.delete()
            else:
                raise e

        # These are too important to leave to a (possibly omitted) is_valid
        # call:
        self._clean_is_localizable()
        # Everything is validated before save() is called, so the only thing
        # that could cause save() to exit prematurely would be an exception,
        # which would cause a rollback, which would negate any category changes
        # we make here, so don't worry:
        self._clean_category()

        super(Document, self).save(*args, **kwargs)

        # Make redirects if there's an approved revision and title or slug
        # changed. Allowing redirects for unapproved docs would (1) be of
        # limited use and (2) require making Revision.creator nullable.
        slug_changed = hasattr(self, 'old_slug')
        title_changed = hasattr(self, 'old_title')
        if self.current_revision and (slug_changed or title_changed):
            doc = Document.objects.create(locale=self.locale,
                                          title=self._attr_for_redirect(
                                              'title', REDIRECT_TITLE),
                                          slug=self._attr_for_redirect(
                                              'slug', REDIRECT_SLUG),
                                          category=self.category,
                                          is_localizable=False)
            Revision.objects.create(document=doc,
                                    content=REDIRECT_CONTENT % dict(
                                        href=self.get_absolute_url(),
                                        title=self.title),
                                    is_approved=True,
                                    reviewer=self.current_revision.creator,
                                    creator=self.current_revision.creator)

            if slug_changed:
                del self.old_slug
            if title_changed:
                del self.old_title

    def __setattr__(self, name, value):
        """Trap setting slug and title, recording initial value."""
        # Public API: delete the old_title or old_slug attrs after changing
        # title or slug (respectively) to suppress redirect generation.
        if getattr(self, 'id', None):
            # I have been saved and so am worthy of a redirect.
            if name in ('slug', 'title') and hasattr(self, name):
                old_name = 'old_' + name
                if not hasattr(self, old_name):
                    # Case insensitive comparison:
                    if getattr(self, name).lower() != value.lower():
                        # Save original value:
                        setattr(self, old_name, getattr(self, name))
                elif value == getattr(self, old_name):
                    # They changed the attr back to its original value.
                    delattr(self, old_name)
        super(Document, self).__setattr__(name, value)

    @property
    def content_parsed(self):
        if not self.current_revision:
            return None

        return self.current_revision.content_parsed

    @property
    def language(self):
        return settings.LANGUAGES[self.locale.lower()]

    # FF version and OS are hung off the original, untranslated document and
    # dynamically inherited by translations:
    firefox_versions = _inherited('firefox_versions', 'firefox_version_set')
    operating_systems = _inherited('operating_systems', 'operating_system_set')

    def get_absolute_url(self):
        # FIXME: There should be no way that the slug is empty.
        slug = self.slug or 'NOSLUG'
        return reverse('wiki.document', locale=self.locale, args=[slug])

    @staticmethod
    def from_url(url, required_locale=None, id_only=False):
        """Return the approved Document the URL represents, None if there isn't
        one.

        Return None if the URL is a 404, the URL doesn't point to the right
        view, or the indicated document doesn't exist.

        To limit the universe of discourse to a certain locale, pass in a
        `required_locale`. To fetch only the ID of the returned Document, set
        `id_only` to True.

        """
        # Extract locale and path from URL:
        path = urlparse(url)[2]  # never has errors AFAICT
        locale, path = split_path(path)
        if required_locale and locale != required_locale:
            return None
        path = '/' + path

        try:
            view, view_args, view_kwargs = resolve(path)
        except Http404:
            return None

        import wiki.views  # Views import models; models import views.
        if view != wiki.views.document:
            return None

        # Map locale-slug pair to Document ID:
        doc_query = Document.objects.exclude(current_revision__isnull=True)
        if id_only:
            doc_query = doc_query.only('id')
        try:
            return doc_query.get(
                locale=locale,
                slug=view_kwargs['document_slug'])
        except Document.DoesNotExist:
            return None

    def redirect_url(self):
        """If I am a redirect, return the absolute URL to which I redirect.

        Otherwise, return None.

        """
        # If a document starts with REDIRECT_HTML and contains any <a> tags
        # with hrefs, return the href of the first one. This trick saves us
        # from having to parse the HTML every time.
        if REDIRECT_HTML in self.html:
            anchors = PyQuery(self.html)('a[href].redirect')
            if anchors:
                return anchors[0].get('href')

    def redirect_document(self):
        """If I am a redirect to a Document, return that Document.

        Otherwise, return None.

        """
        url = self.redirect_url()
        if url:
            return self.from_url(url)

    def __unicode__(self):
        return '[%s] %s' % (self.locale, self.title)

    def allows_revision_by(self, user):
        """Return whether `user` is allowed to create new revisions of me.

        The motivation behind this method is that templates and other types of
        docs may have different permissions.

        """
        # TODO: Add tests for templateness or whatever is required.
        # Leaving this method signature untouched for now in case we do need
        # to use it in the future. ~james
        return True

    def allows_editing_by(self, user):
        """Return whether `user` is allowed to edit document-level metadata.

        If the Document doesn't have a current_revision (nothing approved) then
        all the Document fields are still editable. Once there is an approved
        Revision, the Document fields can only be edited by privileged users.

        """
        return (not self.current_revision or
                user.has_perm('wiki.change_document'))

    def translated_to(self, locale):
        """Return the translation of me to the given locale.

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
        """Return the document I was translated from or, if none, myself."""
        return self.parent or self

    def has_voted(self, request):
        """Did the user already vote for this document?"""
        if request.user.is_authenticated():
            qs = HelpfulVote.objects.filter(document=self,
                                            creator=request.user)
        elif request.anonymous.has_id:
            anon_id = request.anonymous.anonymous_id
            qs = HelpfulVote.objects.filter(document=self,
                                            anonymous_id=anon_id)
        else:
            return False

        return qs.exists()

    def is_majorly_outdated(self):
        """Return whether a MAJOR_SIGNIFICANCE-level update has occurred to the
        parent document since this translation had an approved update.

        If this is not a translation or has never been approved, return False.

        """
        if not (self.parent and self.current_revision):
            return False

        based_on_id = self.current_revision.based_on_id
        more_filters = {'id__gt': based_on_id} if based_on_id else {}
        return self.parent.revisions.filter(
            is_approved=True,
            significance__gte=MAJOR_SIGNIFICANCE, **more_filters).exists()

    def is_watched_by(self, user):
        """Return whether `user` is notified of edits to me."""
        from wiki.events import EditDocumentEvent
        return EditDocumentEvent.is_notifying(user, self)


class ReviewTag(TagBase):
    """A tag indicating review status, mainly for revisions"""
    class Meta:
        verbose_name = _("Review Tag")
        verbose_name_plural = _("Review Tags")


class ReviewTaggedRevision(ItemBase):
    """Through model, just for review tags on revisions"""
    content_object = models.ForeignKey('Revision')
    tag = models.ForeignKey(ReviewTag)

    # FIXME: This is copypasta from taggit/models.py#TaggedItemBase, which I
    # don't like. But, it seems to be the only way to get *both* a custom tag
    # *and* a custom through model.
    # See: https://github.com/boar/boar/blob/master/boar/articles/models.py#L63
    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return ReviewTag.objects.filter(
                reviewtaggedrevision__content_object=instance)
        return ReviewTag.objects.filter(
            reviewtaggedrevision__content_object__isnull=False).distinct()


class Revision(ModelBase):
    """A revision of a localized knowledgebase document"""
    document = models.ForeignKey(Document, related_name='revisions')

    # Title and slug in document are primary, but they're kept here for
    # revision history.
    title = models.CharField(max_length=255, null=True, db_index=True)
    slug = models.CharField(max_length=255, null=True, db_index=True)

    summary = models.TextField()  # wiki markup
    content = models.TextField()  # wiki markup

    # Keywords are used mostly to affect search rankings. Moderators may not
    # have the language expertise to translate keywords, so we put them in the
    # Revision so the translators can handle them:
    keywords = models.CharField(max_length=255, blank=True)

    # Tags are (ab)used as status flags and for searches, but the through model
    # should constrain things from getting expensive.
    review_tags = TaggableManager(through=ReviewTaggedRevision)

    created = models.DateTimeField(default=datetime.now)
    reviewed = models.DateTimeField(null=True)
    significance = models.IntegerField(choices=SIGNIFICANCES, null=True)
    comment = models.CharField(max_length=255)
    reviewer = models.ForeignKey(User, related_name='reviewed_revisions',
                                 null=True)
    creator = models.ForeignKey(User, related_name='created_revisions')
    is_approved = models.BooleanField(default=True, db_index=True)

    # The default locale's rev that was current when the Edit button was hit to
    # create this revision. Used to determine whether localizations are out of
    # date.
    based_on = models.ForeignKey('self', null=True, blank=True)
    # TODO: limit_choices_to={'document__locale':
    # settings.WIKI_DEFAULT_LANGUAGE} is a start but not sufficient.

    # HACK: Migration bookkeeping - index by the old_id of MindTouch revisions
    # so that migrations can be idempotent.
    mindtouch_old_id = models.IntegerField(
            help_text="ID for migrated MindTouch revision (null for current)",
            null=True, db_index=True, unique=True)
    is_mindtouch_migration = models.BooleanField(default=False, db_index=True,
            help_text="Did this revision come from MindTouch?")

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
        base = get_current_or_latest_revision(original)
        has_approved = original.revisions.filter(is_approved=True).exists()
        if (original.current_revision or not has_approved):
            if (self.based_on and
                self.based_on.document != original):
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
                old = self.based_on
                self.based_on = based_on  # Be nice and guess a correct value.
                # TODO(erik): This error message ignores non-translations.
                raise ValidationError(_('A revision must be based on a '
                    'revision of the %(locale)s document. Revision ID'
                    ' %(id)s does not fit those criteria.') %
                    dict(locale=LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
                         id=old.id))

    def save(self, *args, **kwargs):
        _, is_clean = self._based_on_is_clean()
        if not is_clean:  # No more Mister Nice Guy
            # TODO(erik): This error message ignores non-translations.
            raise ProgrammingError('Revision.based_on must be None or refer '
                                   'to a revision of the default-'
                                   'language document.')

        if self.content:
            self.content = (wiki.content
                            .parse(self.content)
                            .injectSectionIDs()
                            .serialize())
        if not self.title:
            self.title = self.document.title
        if not self.slug:
            self.slug = self.document.slug

        super(Revision, self).save(*args, **kwargs)

        # When a revision is approved, update document metadata and re-cache
        # the document's html content
        if self.is_approved and (
                not self.document.current_revision or
                self.document.current_revision.id < self.id):
            self.make_current()

    def make_current(self):
        """Make this revision the current one for the document"""
        self.document.title = self.title
        self.document.slug = self.slug
        self.document.html = self.content_cleaned
        self.document.current_revision = self
        self.document.save()

    def __unicode__(self):
        return u'[%s] %s #%s: %s' % (self.document.locale,
                                      self.document.title,
                                      self.id, self.content[:50])

    def get_section_content(self, section_id):
        """Convenience method to extract the content for a single section"""
        return(wiki.content
            .parse(self.content)
            .extractSection(section_id)
            .serialize())
        
    @property
    def content_cleaned(self):
        return bleach.clean(
            self.content, attributes=ALLOWED_ATTRIBUTES, tags=ALLOWED_TAGS
        )


# FirefoxVersion and OperatingSystem map many ints to one Document. The
# enumeration table of int-to-string is not represented in the DB because of
# difficulty working DB-dwelling gettext keys into our l10n workflow.
class FirefoxVersion(ModelBase):
    """A Firefox version, version range, etc. used to categorize documents"""
    item_id = models.IntegerField(choices=[(v.id, v.name) for v in
                                           FIREFOX_VERSIONS])
    document = models.ForeignKey(Document, related_name='firefox_version_set')

    class Meta(object):
        unique_together = ('item_id', 'document')


class OperatingSystem(ModelBase):
    """An operating system used to categorize documents"""
    item_id = models.IntegerField(choices=[(o.id, o.name) for o in
                                           OPERATING_SYSTEMS])
    document = models.ForeignKey(Document, related_name='operating_system_set')

    class Meta(object):
        unique_together = ('item_id', 'document')


class HelpfulVote(ModelBase):
    """Helpful or Not Helpful vote on Document."""
    document = models.ForeignKey(Document, related_name='poll_votes')
    helpful = models.BooleanField(default=False)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    creator = models.ForeignKey(User, related_name='poll_votes', null=True)
    anonymous_id = models.CharField(max_length=40, db_index=True)
    user_agent = models.CharField(max_length=1000)


class RelatedDocument(ModelBase):
    document = models.ForeignKey(Document, related_name='related_from')
    related = models.ForeignKey(Document, related_name='related_to')
    in_common = models.IntegerField()

    class Meta(object):
        ordering = ['-in_common']


def toolbar_config_upload_to(instance, filename):
    """upload_to builder for toolbar config files"""
    if (instance.default and instance.default == True):
        return 'js/ckeditor_config.js'
    else:
        return 'js/ckeditor_config_%s.js' % instance.creator.id


class EditorToolbar(ModelBase):
    creator = models.ForeignKey(User, related_name='created_toolbars')
    default = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    code = models.TextField(max_length=2000)

    def __unicode__(self):
        return self.name


def get_current_or_latest_revision(document, reviewed_only=True):
    """Returns current revision if there is one, else the last created
    revision."""
    rev = document.current_revision
    if not rev:
        if reviewed_only:
            filter = models.Q(is_approved=False, reviewed__isnull=False)
        else:
            filter = models.Q()
        revs = document.revisions.exclude(filter).order_by('-created')
        if revs.exists():
            rev = revs[0]

    return rev

add_introspection_rules([], ["^utils\.OverwritingFileField"])
