from nose.tools import eq_

from kuma.wiki.events import context_dict
from kuma.wiki.tests import TestCaseBase, revision


class NotificationEmailTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_context_dict_no_previous_revision(self):
        rev = revision()
        try:
            cd = context_dict(rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_(cd, cd)
