# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_

from wiki.tests import TestCaseBase, revision
from wiki.events import context_dict


class NotificationEmailTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_context_dict_no_previous_revision(self):
        rev = revision()
        try:
            cd = context_dict(rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_(cd, cd)
