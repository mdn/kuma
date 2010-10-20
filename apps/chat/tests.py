from django.conf import settings
from django.core.cache import cache

from nose.tools import eq_

from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class ChatTestCase(TestCase):
    def test_uncached(self):
        cache.delete(settings.CHAT_CACHE_KEY)
        resp = self.client.get(reverse('chat.queue-status', locale='en-US'))
        eq_(503, resp.status_code)
        eq_('', resp.content)

    def test_cached(self):
        source = 'The Output'
        cache.set(settings.CHAT_CACHE_KEY, source)
        resp = self.client.get(reverse('chat.queue-status', locale='en-US'))
        eq_(200, resp.status_code)
        eq_(source, resp.content)
