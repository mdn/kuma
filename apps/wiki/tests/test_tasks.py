from copy import deepcopy
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache

import celery.conf
import mock
from nose.tools import eq_
from test_utils import RequestFactory

from sumo.tests import TestCase
from wiki.tasks import (send_reviewed_notification, rebuild_kb,
                        schedule_rebuild_kb, _rebuild_kb_chunk)
from wiki.tests import TestCaseBase, revision


REVIEWED_EMAIL_CONTENT = """

Your revision has been reviewed.

admin has approved your revision to the document
%s.

Message from the reviewer:

%s

To view the history of this document, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/docs/%s$history
"""


class RebuildTestCase(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']
    rf = RequestFactory()
    ALWAYS_EAGER = celery.conf.ALWAYS_EAGER

    def setUp(self):
        self.old_settings = deepcopy(settings._wrapped.__dict__)
        settings.WIKI_REBUILD_ON_DEMAND = True
        celery.conf.ALWAYS_EAGER = True

    def tearDown(self):
        cache.delete(settings.WIKI_REBUILD_TOKEN)
        settings._wrapped.__dict__ = self.old_settings
        celery.conf.ALWAYS_EAGER = self.ALWAYS_EAGER

    @mock.patch_object(rebuild_kb, 'delay')
    def test_eager_queue(self, delay):
        schedule_rebuild_kb()
        assert not cache.get(settings.WIKI_REBUILD_TOKEN)
        assert not delay.called

    @mock.patch_object(rebuild_kb, 'delay')
    def test_task_queue(self, delay):
        celery.conf.ALWAYS_EAGER = False
        schedule_rebuild_kb()
        assert cache.get(settings.WIKI_REBUILD_TOKEN)
        assert delay.called

    @mock.patch_object(rebuild_kb, 'delay')
    def test_already_queued(self, delay):
        cache.set(settings.WIKI_REBUILD_TOKEN, True)
        schedule_rebuild_kb()
        assert cache.get(settings.WIKI_REBUILD_TOKEN)
        assert not delay.called

    @mock.patch_object(rebuild_kb, 'delay')
    @mock.patch_object(cache, 'get')
    def test_dont_queue(self, get, delay):
        settings.WIKI_REBUILD_ON_DEMAND = False
        schedule_rebuild_kb()
        assert not get.called
        assert not delay.called

    @mock.patch_object(_rebuild_kb_chunk, 'apply_async')
    def test_rebuild_chunk(self, apply_async):
        cache.set(settings.WIKI_REBUILD_TOKEN, True)
        rebuild_kb()
        assert not cache.get(settings.WIKI_REBUILD_TOKEN)
        data = set((1, 2, 4, 5))
        assert 'args' in apply_async.call_args[1]
        eq_(data, set(apply_async.call_args[1]['args'][0]))


class ReviewMailTestCase(TestCaseBase):
    """Test that the review mail gets sent."""
    fixtures = ['test_users.json']

    def _approve_and_send(self, revision, reviewer, message):
        revision.reviewer = reviewer
        revision.reviewed = datetime.now()
        revision.is_approved = True
        revision.save()
        send_reviewed_notification(revision, revision.document, message)

    @mock.patch_object(Site.objects, 'get_current')
    def test_reviewed_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        doc = rev.document
        msg = 'great work!'
        self._approve_and_send(rev, User.objects.get(username='admin'), msg)

        eq_(1, len(mail.outbox))
        eq_('Your revision has been approved: %s' % doc.title,
            mail.outbox[0].subject)
        eq_([rev.creator.email], mail.outbox[0].to)
        eq_(REVIEWED_EMAIL_CONTENT % (doc.title, msg, doc.slug),
            mail.outbox[0].body)

    @mock.patch_object(Site.objects, 'get_current')
    def test_reviewed_by_creator_no_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        msg = "great work!"
        self._approve_and_send(rev, rev.creator, msg)

        # Verify no email was sent
        eq_(0, len(mail.outbox))
