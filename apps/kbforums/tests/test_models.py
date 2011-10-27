import datetime

from django.contrib.auth.models import User

from nose.tools import eq_

from kbforums.events import NewPostEvent, NewThreadEvent
from kbforums.models import Thread, Post
from kbforums.tests import KBForumTestCase
from funfactory.urlresolvers import reverse
from sumo.helpers import urlparams
from wiki.models import Document


class KBForumModelTestCase(KBForumTestCase):

    def test_thread_absolute_url(self):
        t = Thread.objects.get(pk=1)
        exp_ = reverse('wiki.discuss.posts', args=[t.document.slug, t.id])
        eq_(exp_, t.get_absolute_url())

    def test_post_absolute_url(self):
        p = Post.objects.get(pk=1)
        url_ = reverse('wiki.discuss.posts',
                       args=[p.thread.document.slug, p.thread.id])
        exp_ = urlparams(url_, hash='post-%s' % p.id)
        eq_(exp_, p.get_absolute_url())

        p = Post.objects.get(pk=24)
        url_ = reverse('wiki.discuss.posts',
                       args=[p.thread.document.slug, p.thread.id])
        exp_ = urlparams(url_, hash='post-%s' % p.id, page=2)
        eq_(exp_, p.get_absolute_url())

    def test_post_page(self):
        p = Post.objects.get(pk=1)
        eq_(1, p.page)
        p = Post.objects.get(pk=22)
        eq_(1, p.page)
        p = Post.objects.get(pk=24)
        eq_(2, p.page)

    def test_last_post_updated(self):
        """Adding/Deleting the last post in a thread should
        update the last_post field
        """
        thread = Thread.objects.get(pk=4)
        user = User.objects.get(pk=118533)

        # add a new post, then check that last_post is updated
        new_post = Post(thread=thread, content="test", creator=user)
        new_post.save()
        thread = Thread.objects.get(pk=thread.id)
        eq_(thread.last_post.id, new_post.id)

        # delete the new post, then check that last_post is updated
        new_post.delete()
        thread = Thread.objects.get(pk=thread.id)
        eq_(thread.last_post.id, 25)

    def test_delete_removes_watches(self):
        """Assert deleting a document deletes watches on its threads."""
        t = Thread.objects.get(pk=1)
        d = t.document
        NewThreadEvent.notify('me@me.com', t)
        assert NewThreadEvent.is_notifying('me@me.com', t)
        d.delete()
        assert not NewThreadEvent.is_notifying('me@me.com', t)


class KBThreadModelTestCase(KBForumTestCase):

    def setUp(self):
        super(KBThreadModelTestCase, self).setUp()
        self.fixtures = self.fixtures + ['kbnotifications.json']

    def test_delete_removes_watches(self):
        t = Thread.objects.get(pk=1)
        NewPostEvent.notify('me@me.com', t)
        assert NewPostEvent.is_notifying('me@me.com', t)
        t.delete()
        assert not NewPostEvent.is_notifying('me@me.com', t)

    def test_delete_last_and_only_post_in_thread(self):
        """Deleting the only post in a thread should delete the thread"""
        doc = Document.objects.get(pk=1)
        thread = Thread(title="test", document=doc, creator_id=118533)
        thread.save()
        post = Post(thread=thread, content="test", creator=thread.creator)
        post.save()
        eq_(1, thread.post_set.count())
        post.delete()
        eq_(0, Thread.objects.filter(pk=thread.id).count())


class KBSaveDateTestCase(KBForumTestCase):
    """
    Test that Thread and Post save methods correctly handle created
    and updated dates.
    """

    delta = datetime.timedelta(milliseconds=100)

    def setUp(self):
        super(KBSaveDateTestCase, self).setUp()

        self.user = User.objects.get(pk=118533)
        self.doc = Document.objects.get(pk=1)
        self.thread = Thread.objects.get(pk=2)

    def assertDateTimeAlmostEqual(self, a, b, delta, msg=None):
        """
        Assert that two datetime objects are within `range` (a timedelta).
        """
        diff = abs(a - b)
        assert diff < abs(delta), msg or '%s ~= %s' % (a, b)

    def test_save_thread_no_created(self):
        """Saving a new thread should behave as if auto_add_now was set."""
        t = self.doc.thread_set.create(title='foo', creator=self.user)
        t.save()
        now = datetime.datetime.now()
        self.assertDateTimeAlmostEqual(now, t.created, self.delta)

    def test_save_thread_created(self):
        """
        Saving a new thread that already has a created date should respect
        that created date.
        """
        created = datetime.datetime(1992, 1, 12, 9, 48, 23)
        t = self.doc.thread_set.create(title='foo', creator=self.user,
                                       created=created)
        t.save()
        eq_(created, t.created)

    def test_save_old_thread_created(self):
        """Saving an old thread should not change its created date."""
        t = Thread.objects.get(pk=3)
        created = t.created
        t.save()
        eq_(created, t.created)

    def test_save_new_post_no_timestamps(self):
        """
        Saving a new post should behave as if auto_add_now was set on
        created and auto_now set on updated.
        """
        p = Post(thread=self.thread, content='bar', creator=self.user)
        p.save()
        now = datetime.datetime.now()
        self.assertDateTimeAlmostEqual(now, p.created, self.delta)
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

    def test_save_old_post_no_timestamps(self):
        """
        Saving an existing post should update the updated date.
        """
        p = Post.objects.get(pk=4)

        updated = datetime.datetime(2010, 5, 4, 14, 4, 31)
        eq_(updated, p.updated)

        p.content = 'baz'
        p.updated_by = self.user
        p.save()

        now = datetime.datetime.now()
        created = datetime.datetime(2010, 5, 4, 14, 4, 22)
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)
        eq_(created, p.created)

    def test_save_new_post_timestamps(self):
        """
        Saving a new post should not allow you to override auto_add_now- and
        auto_now-like functionality.
        """
        created_ = datetime.datetime(1992, 1, 12, 10, 12, 32)
        p = Post(thread=self.thread, content='bar', creator=self.user,
                 created=created_, updated=created_)
        p.save()

        now = datetime.datetime.now()
        self.assertDateTimeAlmostEqual(now, p.created, self.delta)
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

    def test_content_parsed_sanity(self):
        """The content_parsed field is populated."""
        p = Post.objects.get(pk=4)
        eq_('<p>yet another post\n</p>', p.content_parsed)
