"""Tests for the TestCase base class and any other utils that come along."""

from django.core.cache import cache

import test_utils
from nose.tools import eq_


CACHE_KEY = 'sumo_cache_flushing_test'


class CacheFlushingTests(test_utils.TestCase):
    """Tests that make sure SUMO's base TestCase flushes memcached.

    This whole class comprises one conceptual test in two parts, which must
    run in the listed order.

    """
    def test_1_store(self):
        """Store a value in the cache."""
        cache.set(CACHE_KEY, 'smoo')

    def test_2_assert(self):
        """Assert the value stored above isn't there."""
        eq_(None, cache.get(CACHE_KEY))
