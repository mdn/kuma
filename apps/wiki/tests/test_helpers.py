from nose.tools import eq_

from wiki.tests import TestCaseBase, revision
from wiki.helpers import revisions_unified_diff


class RevisionsUnifiedDiffTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_from_revision_none(self):
        rev = revision()
        try:
            diff = revisions_unified_diff(None, rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_("Diff is unavailable.", diff)
