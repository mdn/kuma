import datetime

from django.test import client
from django.contrib.auth.models import User

from nose.tools import eq_

from forums.models import Forum, Thread, Post
from forums.tests import ForumTestCase
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from notifications import create_watch
from notifications.models import EventWatch


class ForumModelTestCase(ForumTestCase):

    def setUp(self):
        super(ForumModelTestCase, self).setUp()

        # Warm up the prefixer for reverse()
        client.Client().get('/')

    def test_forum_absolute_url(self):
        f = Forum.objects.get(pk=1)
        exp_ = reverse('forums.threads', kwargs={'forum_slug': f.slug})
        eq_(exp_, f.get_absolute_url())

    def test_thread_absolute_url(self):
        t = Thread.objects.get(pk=1)
        exp_ = reverse('forums.posts', kwargs={'forum_slug': t.forum.slug,
                                               'thread_id': t.id})
        eq_(exp_, t.get_absolute_url())

    def test_post_absolute_url(self):
        p = Post.objects.get(pk=1)
        url_ = reverse('forums.posts',
                       kwargs={'forum_slug': p.thread.forum.slug,
                               'thread_id': p.thread.id})
        exp_ = urlparams(url_, hash='post-%s' % p.id)
        eq_(exp_, p.get_absolute_url())

        p = Post.objects.get(pk=24)
        url_ = reverse('forums.posts',
                       kwargs={'forum_slug': p.thread.forum.slug,
                               'thread_id': p.thread.id})
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
        """Adding/Deleting the last post in a thread and forum should
        update the last_post field
        """
        forum = Forum.objects.get(pk=1)
        last_post = forum.last_post
        thread = last_post.thread

        # add a new post, then check that last_post is updated
        new_post = Post(thread=thread, content="test", author=last_post.author)
        new_post.save()
        forum = Forum.objects.get(pk=1)
        thread = Thread.objects.get(pk=thread.id)
        eq_(forum.last_post.id, new_post.id)
        eq_(thread.last_post.id, new_post.id)

        # delete the new post, then check that last_post is updated
        new_post.delete()
        forum = Forum.objects.get(pk=1)
        thread = Thread.objects.get(pk=thread.id)
        eq_(forum.last_post.id, last_post.id)
        eq_(thread.last_post.id, last_post.id)

    def test_public_access(self):
        """Assert Forums think they're publicly viewable and postable at
        appropriate times."""
        forum = Forum.objects.get(pk=1)
        unprivileged_user = User.objects.get(pk=118533)
        assert forum.allows_viewing_by(unprivileged_user)
        assert forum.allows_posting_by(unprivileged_user)

    def test_access_restriction(self):
        """Assert Forums are inaccessible to the public when restricted."""
        forum = Forum.objects.get(pk=3)
        unprivileged_user = User.objects.get(pk=118533)
        assert not forum.allows_viewing_by(unprivileged_user)
        assert not forum.allows_posting_by(unprivileged_user)

    def test_move_updates_last_posts(self):
        """Moving the thread containing a forum's last post to a new forum
        should update the last_post of both forums. Consequently, deleting
        the last post shouldn't delete the old forum. [bug 588994]"""
        old_forum = Forum.objects.get(pk=1)  # forum 1 has newest post
        new_forum = Forum.objects.get(pk=2)
        last_post = old_forum.last_post
        thread = last_post.thread
        thread.forum = new_forum
        thread.save()

        # Old forum's last_post updated?
        self.assertNotEqual(Forum.objects.get(pk=1).last_post, last_post)

        # New forum's last_post updated?
        eq_(Forum.objects.get(pk=2).last_post, last_post)

        # Delete the post, and both forums should still exist:
        last_post.delete()
        eq_(1, Forum.objects.filter(pk=1).count())
        eq_(1, Forum.objects.filter(pk=2).count())


class ThreadModelTestCase(ForumTestCase):

    def setUp(self):
        super(ThreadModelTestCase, self).setUp()

        self.fixtures = self.fixtures + ['notifications.json']

        # Warm up the prefixer for reverse()
        client.Client().get('/')

    def test_delete_thread_with_last_forum_post(self):
        """Deleting the thread with a forum's last post should
        update the last_post field on the forum
        """
        forum = Forum.objects.get(pk=1)
        last_post = forum.last_post

        # add a new thread and post, verify last_post updated
        thread = Thread(title="test", forum=forum, creator_id=118533)
        thread.save()
        post = Post(thread=thread, content="test", author=thread.creator)
        post.save()
        forum = Forum.objects.get(pk=1)
        eq_(forum.last_post.id, post.id)

        # delete the post, verify last_post updated
        thread.delete()
        forum = Forum.objects.get(pk=1)
        eq_(forum.last_post.id, last_post.id)
        eq_(Thread.objects.filter(pk=thread.id).count(), 0)

    def test_delete_removes_watches(self):
        create_watch(Thread, 1, 'me@me.com', 'reply')
        eq_(1, EventWatch.uncached.filter(watch_id=1).count())
        t = Thread.objects.get(pk=1)
        t.delete()
        eq_(0, EventWatch.uncached.filter(watch_id=1).count())

    def test_delete_last_and_only_post_in_thread(self):
        """Deleting the only post in a thread should delete the thread"""
        forum = Forum.objects.get(pk=1)
        thread = Thread(title="test", forum=forum, creator_id=118533)
        thread.save()
        post = Post(thread=thread, content="test", author=thread.creator)
        post.save()
        eq_(1, thread.post_set.count())
        post.delete()
        eq_(0, Thread.objects.filter(pk=thread.id).count())


class SaveDateTestCase(ForumTestCase):
    """
    Test that Thread and Post save methods correctly handle created
    and updated dates.
    """

    delta = datetime.timedelta(milliseconds=100)

    def setUp(self):
        super(SaveDateTestCase, self).setUp()

        self.user = User.objects.get(pk=118533)
        self.forum = Forum.objects.get(pk=1)
        self.thread = Thread.objects.get(pk=2)

    def assertDateTimeAlmostEqual(self, a, b, delta, msg=None):
        """
        Assert that two datetime objects are within `range` (a timedelta).
        """
        diff = abs(a - b)
        assert diff < abs(delta), msg or '%s ~= %s' % (a, b)

    def test_save_thread_no_created(self):
        """Saving a new thread should behave as if auto_add_now was set."""
        t = self.forum.thread_set.create(title='foo', creator=self.user)
        t.save()
        now = datetime.datetime.now()
        self.assertDateTimeAlmostEqual(now, t.created, self.delta)

    def test_save_thread_created(self):
        """
        Saving a new thread that already has a created date should respect
        that created date.
        """

        created = datetime.datetime(1992, 1, 12, 9, 48, 23)
        t = self.forum.thread_set.create(title='foo', creator=self.user,
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
        p = Post(thread=self.thread, content='bar', author=self.user)
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
        Saving a new post should allow you to override auto_add_now- and
        auto_now-like functionality.
        """
        created_ = datetime.datetime(1992, 1, 12, 10, 12, 32)
        p = Post(thread=self.thread, content='bar', author=self.user,
                 created=created_, updated=created_)
        p.save()
        eq_(created_, p.created)
        eq_(created_, p.updated)

    def test_content_parsed_sanity(self):
        """The content_parsed field is populated."""
        p = Post.objects.get(pk=4)
        eq_('<p>yet another post\n</p>', p.content_parsed)
