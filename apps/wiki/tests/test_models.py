import logging

from datetime import datetime, timedelta

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr
from taggit.models import TaggedItem

from pyquery import PyQuery as pq

from django.core.exceptions import ValidationError

from sumo import ProgrammingError
from sumo.tests import TestCase
from wiki.cron import calculate_related_documents
from wiki.models import (FirefoxVersion, OperatingSystem, Document,
                         REDIRECT_CONTENT, REDIRECT_SLUG, REDIRECT_TITLE,
                         REDIRECT_HTML, MAJOR_SIGNIFICANCE, CATEGORIES,
                         get_current_or_latest_revision)
from wiki.parser import wiki_to_html
from wiki.tests import document, revision, doc_rev, translated_revision

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter


def _objects_eq(manager, list_):
    """Assert that the objects contained by `manager` are those in `list_`."""
    eq_(set(manager.all()), set(list_))


def redirect_rev(title, redirect_to):
    return revision(
        document=document(title=title, save=True),
        content='REDIRECT [[%s]]' % redirect_to,
        is_approved=True,
        save=True)


class DocumentTests(TestCase):
    """Tests for the Document model"""

    def test_document_is_template(self):
        """is_template stays in sync with the title"""
        d = document(title='test')
        d.save()

        assert not d.is_template

        d.title = 'Template:test'
        d.save()

        assert d.is_template

        d.title = 'Back to document'
        d.save()

        assert not d.is_template

    def test_delete_tagged_document(self):
        """Make sure deleting a tagged doc deletes its tag relationships."""
        # TODO: Move to wherever the tests for TaggableMixin are.
        # This works because Django's delete() sees the `tags` many-to-many
        # field (actually a manager) and follows the reference.
        d = document()
        d.save()
        d.tags.add('grape')
        eq_(1, TaggedItem.objects.count())

        d.delete()
        eq_(0, TaggedItem.objects.count())

    def _test_m2m_inheritance(self, enum_class, attr, direct_attr):
        """Test a descriptor's handling of parent delegation."""
        parent = document()
        child = document(parent=parent, title='Some Other Title')
        e1 = enum_class(item_id=1)
        parent.save()

        # Make sure child sees stuff set on parent:
        getattr(parent, attr).add(e1)
        _objects_eq(getattr(child, attr), [e1])

        # Make sure parent sees stuff set on child:
        child.save()
        e2 = enum_class(item_id=2)
        getattr(child, attr).add(e2)
        _objects_eq(getattr(parent, attr), [e1, e2])

        # Assert the data are attached to the parent, not the child:
        _objects_eq(getattr(parent, direct_attr), [e1, e2])
        _objects_eq(getattr(child, direct_attr), [])

    def test_firefox_version_inheritance(self):
        """Assert the parent delegation of firefox_version works."""
        self._test_m2m_inheritance(FirefoxVersion, 'firefox_versions',
                                   'firefox_version_set')

    def test_operating_system_inheritance(self):
        """Assert the parent delegation of operating_system works."""
        self._test_m2m_inheritance(OperatingSystem, 'operating_systems',
                                   'operating_system_set')

    def test_category_inheritance(self):
        """A document's categories must always be those of its parent."""
        some_category = CATEGORIES[1][0]
        other_category = CATEGORIES[0][0]

        # Notice if somebody ever changes the default on the category field,
        # which would invalidate our test:
        assert some_category != document().category

        parent = document(category=some_category)
        parent.save()
        child = document(parent=parent, locale='de')
        child.save()

        # Make sure child sees stuff set on parent:
        eq_(some_category, child.category)

        # Child'd category should revert to parent's on save:
        child.category = other_category
        child.save()
        eq_(some_category, child.category)

        # Changing the parent category should change the child's:
        parent.category = other_category

        parent.save()
        eq_(other_category,
            parent.translations.get(locale=child.locale).category)

    def _test_int_sets_and_descriptors(self, enum_class, attr):
        """Test our lightweight int sets & descriptors' getting and setting."""
        d = document()
        d.save()
        _objects_eq(getattr(d, attr), [])

        i1 = enum_class(item_id=1)
        getattr(d, attr).add(i1)
        _objects_eq(getattr(d, attr), [i1])

        i2 = enum_class(item_id=2)
        getattr(d, attr).add(i2)
        _objects_eq(getattr(d, attr), [i1, i2])

    def test_firefox_versions(self):
        """Test firefox_versions attr"""
        self._test_int_sets_and_descriptors(FirefoxVersion, 'firefox_versions')

    def test_operating_systems(self):
        """Test operating_systems attr"""
        self._test_int_sets_and_descriptors(OperatingSystem,
                                            'operating_systems')

    def _test_remembering_setter_unsaved(self, field):
        """A remembering setter shouldn't kick in until the doc is saved."""
        old_field = 'old_' + field
        d = document()
        setattr(d, field, 'Foo')
        assert not hasattr(d, old_field), "Doc shouldn't have %s until it's" \
                                          "saved." % old_field

    def test_slug_setter_unsaved(self):
        self._test_remembering_setter_unsaved('slug')

    def test_title_setter_unsaved(self):
        self._test_remembering_setter_unsaved('title')

    def _test_remembering_setter(self, field):
        old_field = 'old_' + field
        d = document()
        d.save()
        old = getattr(d, field)

        # Changing the field makes old_field spring into life:
        setattr(d, field, 'Foo')
        eq_(old, getattr(d, old_field))

        # Changing it back makes old_field disappear:
        setattr(d, field, old)
        assert not hasattr(d, old_field)

        # Change it again once:
        setattr(d, field, 'Foo')

        # And twice:
        setattr(d, field, 'Bar')

        # And old_field should remain as it was, since it hasn't been saved
        # between the two changes:
        eq_(old, getattr(d, old_field))

    def test_slug_setter(self):
        """Make sure changing a slug remembers its old value."""
        self._test_remembering_setter('slug')

    def test_title_setter(self):
        """Make sure changing a title remembers its old value."""
        self._test_remembering_setter('title')

    def test_only_localizable_allowed_children(self):
        """You can't have children for a non-localizable document."""
        # Make English rev:
        en_doc = document(is_localizable=False)
        en_doc.save()

        # Make Deutsch translation:
        de_doc = document(parent=en_doc, locale='de')
        self.assertRaises(ValidationError, de_doc.save)

    def test_cannot_make_non_localizable_if_children(self):
        """You can't make a document non-localizable if it has children."""
        # Make English rev:
        en_doc = document(is_localizable=True)
        en_doc.save()

        # Make Deutsch translation:
        de_doc = document(parent=en_doc, locale='de')
        de_doc.save()
        en_doc.is_localizable = False
        self.assertRaises(ValidationError, en_doc.save)

    def test_non_english_implies_nonlocalizable(self):
        d = document(is_localizable=True, locale='de')
        d.save()
        assert not d.is_localizable

    def test_validate_category_on_save(self):
        """Make sure invalid categories can't be saved.

        Invalid categories cause errors when viewing documents.

        """
        d = document(category=9999)
        self.assertRaises(ValidationError, d.save)

    def test_new_doc_does_not_update_categories(self):
        """Make sure that creating a new document doesn't change the
        category of all the other documents."""
        d1 = document(category=10)
        d1.save()
        assert d1.pk
        d2 = document(category=00)
        assert not d2.pk
        d2._clean_category()
        d1prime = Document.objects.get(pk=d1.pk)
        eq_(10, d1prime.category)


class DocumentTestsWithFixture(TestCase):
    """Document tests which need the users fixture"""

    fixtures = ['test_users.json']

    def test_majorly_outdated(self):
        """Test the is_majorly_outdated method."""
        trans = translated_revision(is_approved=True)
        trans.save()
        trans_doc = trans.document

        # Make sure a doc returns False if it has no parent:
        assert not trans_doc.parent.is_majorly_outdated()

        assert not trans_doc.is_majorly_outdated()

        # Add a parent revision of MAJOR significance:
        r = revision(document=trans_doc.parent,
                     significance=MAJOR_SIGNIFICANCE,
                     is_approved=False)
        r.save()
        assert not trans_doc.is_majorly_outdated()

        # Approve it:
        r.is_approved = True
        r.save()

        assert trans_doc.is_majorly_outdated()

    def test_majorly_outdated_with_unapproved_parents(self):
        """Migrations might introduce translated revisions without based_on
        set. Tolerate these.

        If based_on of a translation's current_revision is None, the
        translation should be considered out of date iff any
        major-significance, approved revision to the English article exists.

        """
        # Create a parent doc with only an unapproved revision...
        parent_rev = revision()
        parent_rev.save()
        # ...and a translation with a revision based on nothing.
        trans = document(parent=parent_rev.document, locale='de')
        trans.save()
        trans_rev = revision(document=trans, is_approved=True)
        trans_rev.save()

        assert trans_rev.based_on is None, \
            ('based_on defaulted to something non-None, which this test '
             "wasn't expecting.")

        assert not trans.is_majorly_outdated(), \
            ('A translation was considered majorly out of date even though '
             'the English document has never had an approved revision of '
             'major significance.')

        major_parent_rev = revision(document=parent_rev.document,
                                    significance=MAJOR_SIGNIFICANCE,
                                    is_approved=True)
        major_parent_rev.save()

        assert trans.is_majorly_outdated(), \
            ('A translation was not considered majorly outdated when its '
             "current revision's based_on value was None.")

    def test_redirect_document_non_redirect(self):
        """Assert redirect_document on non-redirects returns None."""
        eq_(None, document().redirect_document())

    def test_redirect_document_external_redirect(self):
        """Assert redirects to external pages return None."""
        eq_(None, revision(content='REDIRECT [http://example.com]',
                           is_approved=True,
                           save=True).document.redirect_document())

    def test_redirect_document_nonexistent(self):
        """Assert redirects to non-existent pages return None."""
        eq_(None, revision(content='REDIRECT [[kersmoo]]',
                           is_approved=True,
                           save=True).document.redirect_document())


class RedirectCreationTests(TestCase):
    """Tests for automatic creation of redirects when slug or title changes"""
    fixtures = ['test_users.json']

    def setUp(self):
        self.d, self.r = doc_rev()
        self.old_title = self.d.title
        self.old_slug = self.d.slug

    def test_change_slug(self):
        """Test proper redirect creation on slug change."""
        self.d.slug = 'new-slug'
        self.d.save()
        redirect = Document.uncached.get(slug=self.old_slug)
        # "uncached" isn't necessary, but someday a worse caching layer could
        # make it so.
        attrs = dict(title=self.d.title, href=self.d.get_absolute_url())
        eq_(REDIRECT_CONTENT % attrs, redirect.current_revision.content)
        eq_(REDIRECT_TITLE % dict(old=self.d.title, number=1), redirect.title)

    def test_change_title(self):
        """Test proper redirect creation on title change."""
        self.d.title = 'New Title'
        self.d.save()
        redirect = Document.uncached.get(title=self.old_title)
        attrs = dict(title=self.d.title, href=self.d.get_absolute_url())
        eq_(REDIRECT_CONTENT % attrs, redirect.current_revision.content)
        eq_(REDIRECT_SLUG % dict(old=self.d.slug, number=1), redirect.slug)

    def test_change_slug_and_title(self):
        """Assert only one redirect is made when both slug and title change."""
        self.d.title = 'New Title'
        self.d.slug = 'new-slug'
        self.d.save()
        attrs = dict(title=self.d.title, href=self.d.get_absolute_url())
        eq_(REDIRECT_CONTENT % attrs,
            Document.uncached.get(
                slug=self.old_slug,
                title=self.old_title).current_revision.content)

    def test_no_redirect_on_unsaved_change(self):
        """No redirect should be made when an unsaved doc's title or slug is
        changed."""
        d = document(title='Gerbil')
        d.title = 'Weasel'
        d.save()
        # There should be no redirect from Gerbil -> Weasel:
        assert not Document.uncached.filter(title='Gerbil').exists()

    def _test_collision_avoidance(self, attr, other_attr, template):
        """When creating redirects, dodge existing docs' titles and slugs."""
        # Create a doc called something like Whatever Redirect 1:
        document(locale=self.d.locale,
                **{other_attr: template % dict(old=getattr(self.d, other_attr),
                                               number=1)}).save()

        # Trigger creation of a redirect of a new title or slug:
        setattr(self.d, attr, 'new')
        self.d.save()

        # It should be called something like Whatever Redirect 2:
        redirect = Document.uncached.get(**{attr: getattr(self,
                                                          'old_' + attr)})
        eq_(template % dict(old=getattr(self.d, other_attr),
                            number=2), getattr(redirect, other_attr))

    def test_slug_collision_avoidance(self):
        """Dodge existing slugs when making redirects due to title changes."""
        self._test_collision_avoidance('slug', 'title', REDIRECT_TITLE)

    def test_title_collision_avoidance(self):
        """Dodge existing titles when making redirects due to slug changes."""
        self._test_collision_avoidance('title', 'slug', REDIRECT_SLUG)

    def test_redirects_unlocalizable(self):
        """Auto-created redirects should be marked unlocalizable."""
        self.d.slug = 'new-slug'
        self.d.save()
        redirect = Document.uncached.get(slug=self.old_slug)
        eq_(False, redirect.is_localizable)


class RevisionTests(TestCase):
    """Tests for the Revision model"""
    fixtures = ['test_users.json']

    def test_approved_revision_updates_html(self):
        """Creating an approved revision updates document.html"""
        d, _ = doc_rev('Replace document html')

        assert 'Replace document html' in d.html, \
               '"Replace document html" not in %s' % d.html

        # Creating another approved revision replaces it again
        r = revision(document=d, content='Replace html again',
                     is_approved=True)
        r.save()

        assert 'Replace html again' in d.html, \
               '"Replace html again" not in %s' % d.html

    def test_unapproved_revision_not_updates_html(self):
        """Creating an unapproved revision does not update document.html"""
        d, _ = doc_rev('Here to stay')

        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

        # Creating another approved revision keeps initial content
        r = revision(document=d, content='Fail to replace html', is_approved=False)
        r.save()

        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

    def test_revision_unicode(self):
        """Revision containing unicode characters is saved successfully."""
        str = u'Firefox informa\xe7\xf5es \u30d8\u30eb'
        _, r = doc_rev(str)
        eq_(str, r.content)

    def test_save_bad_based_on(self):
        """Saving a Revision with a bad based_on value raises an error."""
        r = revision()
        r.based_on = revision()  # Revision of some other unrelated Document
        self.assertRaises(ProgrammingError, r.save)

    def test_correct_based_on_to_none(self):
        """Assure Revision.clean() changes a bad based_on value to None when
        there is no current_revision of the English document."""
        r = revision()
        r.based_on = revision()  # Revision of some other unrelated Document
        self.assertRaises(ValidationError, r.clean)
        eq_(None, r.based_on)

    def test_correct_based_on_to_current_revision(self):
        """Assure Revision.clean() changes a bad based_on value to the English
        doc's current_revision when there is one."""
        # Make English rev:
        en_rev = revision(is_approved=True)
        en_rev.save()

        # Make Deutsch translation:
        de_doc = document(parent=en_rev.document, locale='de')
        de_doc.save()
        de_rev = revision(document=de_doc)

        # Set based_on to some random, unrelated Document's rev:
        de_rev.based_on = revision()

        # Try to recover:
        self.assertRaises(ValidationError, de_rev.clean)

        eq_(en_rev.document.current_revision, de_rev.based_on)


class RelatedDocumentTests(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def test_related_documents_calculated(self):
        d = Document.uncached.get(pk=1)
        eq_(0, d.related_documents.count())

        calculate_related_documents()

        d = Document.uncached.get(pk=1)
        eq_(2, d.related_documents.count())

    def test_related_only_locale(self):
        calculate_related_documents()
        d = Document.uncached.get(pk=1)
        for rd in d.related_documents.all():
            eq_('en-US', rd.locale)

    def test_only_approved_revisions(self):
        calculate_related_documents()
        d = Document.uncached.get(pk=1)
        for rd in d.related_documents.all():
            assert rd.current_revision

    def test_only_approved_have_related(self):
        calculate_related_documents()
        d = Document.uncached.get(pk=3)
        eq_(0, d.related_documents.count())


class GetCurrentOrLatestRevisionTests(TestCase):
    fixtures = ['test_users.json']

    """Tests for get_current_or_latest_revision."""
    def test_single_approved(self):
        """Get approved revision."""
        rev = revision(is_approved=True, save=True)
        eq_(rev, get_current_or_latest_revision(rev.document))

    def test_single_rejected(self):
        """No approved revisions available should return None."""
        rev = revision(is_approved=False)
        eq_(None, get_current_or_latest_revision(rev.document))

    def test_multiple_approved(self):
        """When multiple approved revisions exist, return the most recent."""
        r1 = revision(is_approved=True, save=True)
        r2 = revision(is_approved=True, save=True, document=r1.document)
        eq_(r2, get_current_or_latest_revision(r2.document))

    def test_approved_over_most_recent(self):
        """Should return most recently approved when there is a more recent
        unreviewed revision."""
        r1 = revision(is_approved=True, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, reviewed=None, save=True,
                      document=r1.document)
        eq_(r1, get_current_or_latest_revision(r2.document))

    def test_latest(self):
        """Return latest not-rejected revision when no current exists."""
        r1 = revision(is_approved=False, reviewed=None, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, reviewed=None, save=True,
                      document=r1.document)
        eq_(r2, get_current_or_latest_revision(r1.document))

    def test_latest_rejected(self):
        """Return latest rejected revision when no current exists."""
        r1 = revision(is_approved=False, reviewed=None, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, save=True, document=r1.document)
        eq_(r2, get_current_or_latest_revision(r1.document,
                                               reviewed_only=False))

    def test_latest_unreviewed(self):
        """Return latest unreviewed revision when no current exists."""
        r1 = revision(is_approved=False, reviewed=None, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, reviewed=None, save=True,
                      document=r1.document)
        eq_(r2, get_current_or_latest_revision(r1.document,
                                               reviewed_only=False))
