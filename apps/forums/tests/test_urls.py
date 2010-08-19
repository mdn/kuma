from nose.tools import eq_

from forums.models import Forum
from forums.tests import ForumTestCase
from sumo.tests import get, post


class BelongsTestCase(ForumTestCase):
    """
    Mixing and matching thread, forum, and post data in URLs should fail.
    """

    def setUp(self):
        super(BelongsTestCase, self).setUp()
        self.forum = Forum.objects.all()[0]
        self.forum_2 = Forum.objects.all()[1]
        self.thread = self.forum.thread_set.filter(is_locked=False)[0]
        self.thread_2 = self.forum.thread_set.filter(is_locked=False)[1]
        self.post = self.thread.post_set.all()[0]
        # Login for testing 403s
        self.client.login(username='admin', password='testpass')

    def test_posts_thread_belongs_to_forum(self):
        """Posts view - thread belongs to forum."""
        r = get(self.client, 'forums.posts',
                args=[self.forum_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_reply_thread_belongs_to_forum(self):
        """Reply action - thread belongs to forum."""
        r = post(self.client, 'forums.reply', {},
                 args=[self.forum_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_locked_thread_belongs_to_forum(self):
        """Lock action - thread belongs to forum."""
        r = post(self.client, 'forums.lock_thread', {},
                 args=[self.forum_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_sticky_thread_belongs_to_forum(self):
        """Sticky action - thread belongs to forum."""
        r = post(self.client, 'forums.sticky_thread', {},
                 args=[self.forum_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_edit_thread_belongs_to_forum(self):
        """Edit thread action - thread belongs to forum."""
        r = get(self.client, 'forums.edit_thread',
                args=[self.forum_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_delete_thread_belongs_to_forum(self):
        """Delete thread action - thread belongs to forum."""
        r = get(self.client, 'forums.delete_thread',
                args=[self.forum_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_edit_post_belongs_to_thread_and_forum(self):
        """
        Edit post action - post belongs to thread and thread belongs to
        forum.
        """
        r = get(self.client, 'forums.edit_post',
                args=[self.forum_2.slug, self.thread.id, self.post.id])
        eq_(404, r.status_code)

        r = get(self.client, 'forums.edit_post',
                args=[self.forum.slug, self.thread_2.id, self.post.id])
        eq_(404, r.status_code)

    def test_delete_post_belongs_to_thread_and_forum(self):
        """
        Delete post action - post belongs to thread and thread belongs to
        forum.
        """
        r = get(self.client, 'forums.delete_post',
                args=[self.forum_2.slug, self.thread.id, self.post.id])
        eq_(404, r.status_code)

        r = get(self.client, 'forums.delete_post',
                args=[self.forum.slug, self.thread_2.id, self.post.id])
        eq_(404, r.status_code)
