from nose.tools import eq_

from kuma.users.tests import UserTestCase
from kuma.wiki.events import context_dict
from kuma.wiki.tests import WikiTestCase, revision


class NotificationEmailTests(UserTestCase, WikiTestCase):

    def test_context_dict_no_previous_revision(self):
        rev = revision()
        try:
            cd = context_dict(rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_(cd, cd)
