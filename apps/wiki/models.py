from collections import namedtuple
from datetime import datetime
from itertools import chain

from tower import ugettext_lazy as _lazy

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from sumo.models import ModelBase, TaggableMixin
from sumo.urlresolvers import reverse
from wiki import TEMPLATE_TITLE_PREFIX


# Disruptiveness of edits to translated versions. Keys indicate the relative
# severity.
SIGNIFICANCES = (
    (10, _lazy('Minor details like punctuation and spelling errors')),
    (20, _lazy("Content changes that don't require immediate translation")),
    (30, _lazy('Major content changes that will make older translations '
               'inaccurate')),
    (40, _lazy('New document')))

CATEGORIES = (
    (1, _lazy('Troubleshooting')),)

# FF versions used to filter article searches, power {for} tags, etc.:
#
# Iterables of (ID, name, abbreviation for {for} tags, max version this version
# group encompasses) grouped into optgroups. To add the ability to sniff a new
# version of an existing browser (assuming it doesn't change the user agent
# string too radically), you should need only to add a line here; no JS
# required. Just be wary of inexact floating point comparisons when setting
# max_version, which should be read as "From the next smaller max_version up to
# but not including version x.y".
VersionMetadata = namedtuple('VersionMetadata', 'id, name, slug, max_version')
GROUPED_FIREFOX_VERSIONS = (
    (_lazy('Desktop:'), (
        # The first option is the default for {for} display. This should be the
        # newest version.
        VersionMetadata(1, _lazy('Firefox 4.0'), 'fx4', 4.9999),
        VersionMetadata(2, _lazy('Firefox 3.5-3.6'), 'fx35', 3.9999),
        VersionMetadata(3, _lazy('Firefox 3.0'), 'fx3', 3.4999))),
    (_lazy('Mobile:'), (
        VersionMetadata(4, _lazy('Firefox Mobile 1.1'), 'm11', 1.9999),
        VersionMetadata(5, _lazy('Firefox Mobile 1.0'), 'm1', 1.0999))))

# Flattened:  # TODO: perhaps use optgroups everywhere instead
FIREFOX_VERSIONS = tuple(chain(*[options for label, options in
                                 GROUPED_FIREFOX_VERSIONS]))

# OSes used to filter articles and declare {for} sections:
OsMetaData = namedtuple('OsMetaData', 'id, name, slug')
OPERATING_SYSTEMS = (
    # The first is the default for {for} display.
    OsMetaData(1, _lazy('Windows'), 'win'),
    OsMetaData(2, _lazy('Mac OS X'), 'mac'),
    OsMetaData(3, _lazy('Linux'), 'linux'),
    OsMetaData(4, _lazy('Maemo'), 'maemo'),
    OsMetaData(5, _lazy('Android'), 'android'))


def _inherited(parent_attr, direct_attr):
    """Return a descriptor delegating to an attr of the original document.

    If `self` is a translation, the descriptor delegates to the attribute
    `parent_attr` from the original document. Otherwise, it delegates to the
    attribute `direct_attr` from `self`.

    """
    getter = lambda self: (getattr(self.parent, parent_attr)
                               if self.parent
                           else getattr(self, direct_attr))
    setter = lambda self, val: (setattr(self.parent, parent_attr,
                                        val) if self.parent else
                                setattr(self, direct_attr, val))
    return property(getter, setter)


class Document(ModelBase, TaggableMixin):
    """A localized knowledgebase document, not revision-specific."""
    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # Is this document a template or not?
    # TODO: Localizing templates does not allow changing titles
    is_template = models.BooleanField(default=False, editable=False,
                                      db_index=True)

    # TODO: validate (against settings.SUMO_LANGUAGES?)
    locale = models.CharField(max_length=7, db_index=True,
                              default=settings.WIKI_DEFAULT_LANGUAGE,
                              choices=settings.LANGUAGE_CHOICES)

    # Latest approved revision. (Remove "+" to enable reverse link.)
    current_revision = models.ForeignKey('Revision', null=True,
                                         related_name='current_for+')

    # The Document I was translated from. NULL iff this doc is in the default
    # locale. TODO: validate against settings.WIKI_DEFAULT_LANGUAGE.
    parent = models.ForeignKey('self', related_name='translations', null=True)

    # Cached HTML rendering of wiki markup:
    html = models.TextField(editable=False)

    # Uncomment if/when we need a denormalized flag for how significantly
    # outdated this translation is. We probably will to support the dashboard.
    # If you do this, also make a periodic task to audit it occasionally.
    #
    # outdated = IntegerField(choices=SIGNIFICANCES, editable=False)

    category = models.IntegerField(choices=CATEGORIES)
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

    def save(self, *args, **kwargs):
        self.is_template = self.title.startswith(TEMPLATE_TITLE_PREFIX)
        super(Document, self).save(*args, **kwargs)

    @property
    def content_parsed(self):
        return self.html

    @property
    def language(self):
        return settings.LANGUAGES[self.locale.lower()]

    # FF version and OS are hung off the original, untranslated document and
    # dynamically inherited by translations:
    firefox_versions = _inherited('firefox_versions', 'firefox_version_set')
    operating_systems = _inherited('operating_systems', 'operating_system_set')

    def get_absolute_url(self):
        return reverse('wiki.document', locale=self.locale, args=[self.slug])

    def __unicode__(self):
        return '[%s] %s' % (self.locale, self.title)


class Revision(ModelBase):
    """A revision of a localized knowledgebase document"""
    document = models.ForeignKey(Document, related_name='revisions')
    summary = models.TextField()  # wiki markup
    content = models.TextField()  # wiki markup

    # Keywords are used mostly to affect search rankings. Moderators may not
    # have the language expertise to translate keywords, so we put them in the
    # Revision so the translators can handle them:
    keywords = models.CharField(max_length=255, blank=True)

    created = models.DateTimeField(default=datetime.now)
    reviewed = models.DateTimeField(null=True)
    significance = models.IntegerField(choices=SIGNIFICANCES)
    comment = models.CharField(max_length=255)
    reviewer = models.ForeignKey(User, related_name='reviewed_revisions',
                                 null=True)
    creator = models.ForeignKey(User, related_name='created_revisions')
    is_approved = models.BooleanField(default=False)

    # The default locale's rev that was current when the Edit button was hit to
    # create this revision. Used to determine whether localizations are out of
    # date.
    based_on = models.ForeignKey('self', null=True)  # limited_to default
                                                     # locale's revs

    def save(self, *args, **kwargs):
        super(Revision, self).save(*args, **kwargs)

        # When a revision is approved, re-cache the document's html content
        if self.is_approved and (
                not self.document.current_revision or
                self.document.current_revision.id < self.id):
            from wiki.parser import wiki_to_html
            self.document.html = wiki_to_html(self.content)
            self.document.current_revision = self
            self.document.save()

    def __unicode__(self):
        return u'[%s] %s: %s' % (self.document.locale, self.document.title,
                                 self.content[:50])

    @property
    def content_parsed(self):
        from wiki.parser import wiki_to_html
        return wiki_to_html(self.content)


# FirefoxVersion and OperatingSystem map many ints to one Document. The
# enumeration table of int-to-string is not represented in the DB because of
# difficulty working DB-dwelling gettext keys into our l10n workflow.
class FirefoxVersion(ModelBase):
    """A Firefox version, version range, etc. used to categorize documents"""
    item_id = models.IntegerField(choices=[(v.id, v.name) for v in
                                           FIREFOX_VERSIONS],
                                  db_index=True)
    document = models.ForeignKey(Document, related_name='firefox_version_set')


class OperatingSystem(ModelBase):
    """An operating system used to categorize documents"""
    item_id = models.IntegerField(choices=[(o.id, o.name) for o in
                                           OPERATING_SYSTEMS],
                                  db_index=True)
    document = models.ForeignKey(Document, related_name='operating_system_set')
