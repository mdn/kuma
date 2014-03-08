
from django.conf import settings
from django.core.cache import cache

import celery.conf
import mock
from nose.tools import eq_
from test_utils import RequestFactory

from sumo.tests import TestCase
from devmo.tests import override_settings
from wiki.tasks import rebuild_kb, schedule_rebuild_kb, _rebuild_kb_chunk


class RebuildTestCase(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']
    rf = RequestFactory()
    ALWAYS_EAGER = celery.conf.ALWAYS_EAGER

    def setUp(self):
        celery.conf.ALWAYS_EAGER = True

    def tearDown(self):
        cache.delete(settings.WIKI_REBUILD_TOKEN)
        celery.conf.ALWAYS_EAGER = self.ALWAYS_EAGER

    @mock.patch_object(rebuild_kb, 'delay')
    @override_settings(WIKI_REBUILD_ON_DEMAND=True)
    def test_eager_queue(self, delay):
        schedule_rebuild_kb()
        assert not cache.get(settings.WIKI_REBUILD_TOKEN)
        assert not delay.called

    @override_settings(WIKI_REBUILD_ON_DEMAND=True)
    @mock.patch_object(rebuild_kb, 'delay')
    def test_task_queue(self, delay):
        celery.conf.ALWAYS_EAGER = False
        schedule_rebuild_kb()
        assert cache.get(settings.WIKI_REBUILD_TOKEN)
        assert delay.called

    @override_settings(WIKI_REBUILD_ON_DEMAND=True)
    @mock.patch_object(rebuild_kb, 'delay')
    def test_already_queued(self, delay):
        cache.set(settings.WIKI_REBUILD_TOKEN, True)
        schedule_rebuild_kb()
        assert cache.get(settings.WIKI_REBUILD_TOKEN)
        assert not delay.called

    @override_settings(WIKI_REBUILD_ON_DEMAND=True)
    @mock.patch_object(rebuild_kb, 'delay')
    @mock.patch_object(cache, 'get')
    def test_dont_queue(self, get, delay):
        settings.WIKI_REBUILD_ON_DEMAND = False
        schedule_rebuild_kb()
        assert not get.called
        assert not delay.called

    @override_settings(WIKI_REBUILD_ON_DEMAND=True)
    @mock.patch_object(_rebuild_kb_chunk, 'apply_async')
    def test_rebuild_chunk(self, apply_async):
        cache.set(settings.WIKI_REBUILD_TOKEN, True)
        rebuild_kb()
        assert not cache.get(settings.WIKI_REBUILD_TOKEN)
        data = set((8, 1, 2, 4, 5))
        assert 'args' in apply_async.call_args[1]
        eq_(data, set(apply_async.call_args[1]['args'][0]))
