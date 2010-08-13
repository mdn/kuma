from django.conf import settings
from django.test import TestCase

from nose.tools import eq_
from taggit.models import TaggedItem

from wiki.models import Document, Revision, FirefoxVersion, SIGNIFICANCES


# An arbitrary significance
SOME_SIGNIFICANCE = SIGNIFICANCES[0][0]


class DocumentTests(TestCase):
    """Tests for the Document model"""

    def _document(self, **kwargs):
        """Return an empty document with enough stuff filled out that it can be
        saved."""
        if 'category' not in kwargs:
            kwargs['category'] = SOME_SIGNIFICANCE
        return Document(**kwargs)

    def test_delete_tagged_document(self):
        """Make sure deleting a tagged doc deletes its tag relationships."""
        # TODO: Move to wherever the tests for TaggableMixin are.
        # This works because Django's delete() sees the `tags` many-to-many
        # field (actually a manager) and follows the reference.
        d = self._document()
        d.save()
        d.tags.add('grape')
        eq_(1, TaggedItem.objects.count())

        d.delete()
        eq_(0, TaggedItem.objects.count())

    def test_firefox_versions(self):
        """Make sure our lightweight integer sets work.

        If this works, it's a good bet `operating_systems` does as well.

        """
        d = self._document()
        d.save()
        eq_(list(d.firefox_versions.all()), [])

        v1 = FirefoxVersion(item_id=1)
        d.firefox_versions = [v1]
        eq_(set(d.firefox_versions.all()), set([v1]))

        v2 = FirefoxVersion(item_id=2)
        d.firefox_versions.add(v2)
        eq_(set(d.firefox_versions.all()), set([v1, v2]))


class RevisionTests(TestCase):
    """Tests for the Revision model"""
