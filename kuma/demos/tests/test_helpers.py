import bitly_api
from django.conf import settings
import mock
from nose.tools import eq_, ok_
import test_utils

from kuma.core.cache import memcache
from ..helpers import tag_description, bitly_shorten, bitly


class HelperTestCase(test_utils.TestCase):

    def test_tag_description_no_description(self):
        settings.TAG_DESCRIPTIONS = {
            "tag_name": "test_tag",
            "title": "Testing tag without description",
        }
        description = tag_description("test_tag")
        eq_("test_tag", description)

    def test_tag_description_challenge_none(self):
        tag = 'challenge:none'
        description = tag_description(tag)
        eq_('Removed from Derby', description)

    @mock.patch.object(memcache, 'set')  # prevent caching
    @mock.patch.object(bitly, 'shorten')
    def test_bitly_shorten(self, shorten, cache_set):
        long_url = 'http://example.com/long-url'
        short_url = 'http://bit.ly/short-url'

        # the usual case of returning a dict with a URL
        def short_mock(*args, **kwargs):
            return {'url': short_url}
        shorten.side_effect = short_mock

        eq_(bitly_shorten(long_url), short_url)
        shorten.assert_called_with(long_url)

        # in case of a key error
        def short_mock(*args, **kwargs):
            return {}
        shorten.side_effect = short_mock
        eq_(bitly_shorten(long_url), long_url)
        shorten.assert_called_with(long_url)

        # in case of an upstream error
        shorten.side_effect = bitly_api.BitlyError('500', 'fail fail fail')
        eq_(bitly_shorten(long_url), long_url)
