from datetime import datetime

from tower import ugettext_lazy as _lazy

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from sumo.models import ModelBase, TaggableMixin


# Disruptiveness of edits to translated versions. Keys indicate the relative
# severity.
SIGNIFICANCES = (
    (10, _lazy('Minor details like punctuation and spelling errors')),
    (20, _lazy("Content changes that don't require immediate translation")),
    (30, _lazy('Major content changes that will make older translations '
               'inaccurate')))

CATEGORIES = (
    (1, _lazy('Troubleshooting')),)

# General FF versions used to filter article searches, etc.:
# TODO: If we store these here rather than in the DB, how do we turn the "all"
# case into Sphinx multi-value attrs?
FIREFOX_VERSIONS = (
    (1, _lazy('Firefox 4.0')),
    (2, _lazy('Firefox 3.5-3.6')),
    (3, _lazy('Firefox 3.0')),
    (4, _lazy('Firefox Mobile 1.1')),
    (5, _lazy('Firefox Mobile 1.0')))

# OSes used to filter articles:
OPERATING_SYSTEMS = (
    (1, _lazy('Windows')),
    (2, _lazy('Mac OS X')),
    (3, _lazy('Linux')),
    (4, _lazy('Maemo')),
    (5, _lazy('Android')))


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

    # TODO: validate (against settings.SUMO_LANGUAGES?)
    locale = models.CharField(max_length=7, db_index=True,
                              default=settings.WIKI_DEFAULT_LANGUAGE)

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
        unique_together = (('parent', 'locale'), ('title', 'locale'))

    # Keep this for polymorphism with Questions for search results?
    # @property
    # def content_parsed(self):
    #     return self.html

    # FF version and OS are hung off the original, untranslated document and
    # dynamically inherited by translations:
    firefox_versions = _inherited('firefox_versions', 'firefox_version_set')
    operating_systems = _inherited('operating_systems', 'operating_system_set')


# Caveats:
#  * There's no immutable per-document revision ID revision (e.g., 0..63). We
#    can number them in the view, but deleting one will cause the later ones to
#    be renumbered. We can still use the pkey as an immutable unique value. Is
#    this a problem? If so, we could let admins make a rev inaccessible rather
#    than actually deleting it.
class Revision(ModelBase):
    """A revision of a localized knowledgebase document"""
    document = models.ForeignKey(Document, related_name='revisions')
    summary = models.TextField()  # wiki markup
    content = models.TextField()  # wiki markup

    # Keywords are used mostly to affect search rankings. Moderators may not
    # have the language expertise to translate keywords, so we put them in the
    # Revision so the translators can handle them:
    keywords = models.CharField(max_length=255)

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


# FirefoxVersion and OperatingSystem map many ints to one Document. The
# enumeration table of int-to-string is not represented in the DB because of
# difficulty working DB-dwelling gettext keys into our l10n workflow.
class FirefoxVersion(ModelBase):
    """A Firefox version, version range, etc. used to categorize documents"""
    item_id = models.IntegerField(choices=FIREFOX_VERSIONS, db_index=True)
    document = models.ForeignKey(Document, related_name='firefox_version_set')


class OperatingSystem(ModelBase):
    """An operating system used to categorize documents"""
    item_id = models.IntegerField(choices=OPERATING_SYSTEMS, db_index=True)
    document = models.ForeignKey(Document, related_name='operating_system_set')
