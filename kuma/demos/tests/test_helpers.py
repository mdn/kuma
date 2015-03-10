from django.conf import settings

from kuma.core.tests import KumaTestCase
from ..helpers import tag_description


class TagDescriptionTestCase(KumaTestCase):

    def test_tag_description_no_description(self):
        settings.TAG_DESCRIPTIONS = {
            "tag_name": "test_tag",
            "title": "Testing tag without description",
        }
        description = tag_description("test_tag")
        self.assertEqual("test_tag", description)

    def test_tag_description_challenge_none(self):
        tag = 'challenge:none'
        description = tag_description(tag)
        self.assertEqual('Removed from Derby', description)
