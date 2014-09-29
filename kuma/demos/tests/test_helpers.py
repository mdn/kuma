import test_utils
from nose.tools import eq_

from django.conf import settings

from ..helpers import tag_description


class HelperTestCase(test_utils.TestCase):

    def test_tag_description_no_description(self):
        settings.TAG_DESCRIPTIONS = {"tag_name": "test_tag",
                 "title": "Testing tag without description"}
        description = tag_description("test_tag")
        eq_("test_tag", description)

    def test_tag_description_challenge_none(self):
        tag = 'challenge:none'
        description = tag_description(tag)
        eq_('Removed from Derby', description)
