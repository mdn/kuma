from nose.tools import eq_
from taggit.models import TaggedItem

from sumo.tests import TestCase
from wiki.models import FirefoxVersion, OperatingSystem
from wiki.tests import document, revision


def _objects_eq(manager, list_):
    """Assert that the objects contained by `manager` are those in `list_`."""
    eq_(set(manager.all()), set(list_))


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

    def _test_inheritance(self, enum_class, attr, direct_attr):
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
        self._test_inheritance(FirefoxVersion, 'firefox_versions',
                               'firefox_version_set')

    def test_operating_system_inheritance(self):
        """Assert the parent delegation of operating_system works."""
        self._test_inheritance(OperatingSystem, 'operating_systems',
                               'operating_system_set')

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


def doc_rev(html, content):
    """Helper creates a document and revision given html and content."""
    d = document(html=html)
    d.save()
    r = revision(document=d, content=content, is_approved=True)
    r.save()
    return (d, r)


class RevisionTests(TestCase):
    """Tests for the Revision model"""
    fixtures = ['users.json']

    def test_approved_revision_updates_html(self):
        """Creating an approved revision updates document.html"""
        d, _ = doc_rev('This goes away', 'Replace document html')

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
        d, _ = doc_rev('', 'Here to stay')

        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

        # Creating another approved revision keeps initial content
        r = revision(document=d, content='Fail to replace html')
        r.save()

        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

    def test_revision_unicode(self):
        """Revision containing unicode characters is saved successfully."""
        str = u' \r\nFirefox informa\xe7\xf5es \u30d8\u30eb'
        _, r = doc_rev('', str)
        eq_(str, r.content)
