import logging

from nose.tools import eq_, ok_

from django.contrib.auth.models import User

from wiki.tests import TestCaseBase, revision
from wiki.helpers import (revisions_unified_diff,
                          document_zone_management_links)
from wiki.models import DocumentZone, Document, Revision


class RevisionsUnifiedDiffTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_from_revision_none(self):
        rev = revision()
        try:
            diff = revisions_unified_diff(None, rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_("Diff is unavailable.", diff)

class DocumentZoneTests(TestCaseBase):
    """Tests for DocumentZone helpers"""
    fixtures = ['test_users.json']

    def setUp(self):
        super(DocumentZoneTests, self).setUp()

        root_rev = revision(title='ZoneRoot', slug='ZoneRoot',
                            content='This is the Zone Root',
                            is_approved=True, save=True)
        self.root_doc = root_rev.document

        self.root_zone = DocumentZone(document=self.root_doc)
        self.root_zone.save()

        sub_rev = revision(title='SubPage', slug='SubPage',
                           content='This is a subpage',
                           is_approved=True, save=True)
        self.sub_doc = sub_rev.document
        self.sub_doc.parent_topic = self.root_doc
        self.sub_doc.save()

        other_rev = revision(title='otherPage', slug='otherPage',
                            content='This is an other page',
                            is_approved=True, save=True)
        self.other_doc = other_rev.document
        self.other_doc.save()

    def test_document_zone_links(self):
        admin = User.objects.filter(is_superuser=True)[0]
        random = User.objects.filter(is_superuser=False)[0]
        cases = [
            (admin,  self.root_doc,  False, True),
            (random, self.root_doc,  False, False),
            (admin,  self.sub_doc,   True,  True),
            (random, self.sub_doc,   False, False),
            (admin,  self.other_doc, True,  False),
            (random, self.other_doc, False, False),
        ]
        for (user, doc, add, change) in cases:
            result_links = document_zone_management_links(user, doc)
            eq_(add, (result_links['add'] is not None))
            eq_(change, (result_links['change'] is not None))
