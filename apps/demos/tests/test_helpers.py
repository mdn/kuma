# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_

from django.conf import settings

from sumo.tests import TestCase
from demos.helpers import tag_description

class HelperTestCase(TestCase):

    def test_tag_description_no_description(self):
        settings.TAG_DESCRIPTIONS = {"tag_name": "test_tag",
                 "title": "Testing tag without description"}
        description = tag_description("test_tag")
        eq_("test_tag", description)

    def test_tag_description_challenge_none(self):
        tag = 'challenge:none'
        description = tag_description(tag)
        eq_('Removed from Derby', description)
