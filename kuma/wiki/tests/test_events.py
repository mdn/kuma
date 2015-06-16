from nose.tools import eq_

from kuma.users.tests import UserTestCase
from . import WikiTestCase, revision
from ..events import context_dict


class NotificationEmailTests(UserTestCase, WikiTestCase):

    def test_context_dict_no_previous_revision(self):
        rev = revision(save=True)
        try:
            cd = context_dict(rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_(cd, cd)
