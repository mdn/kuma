from nose.tools import eq_

from kbforums.tests import KBForumTestCase
from sumo.tests import get, post
from wiki.models import Document


class KBBelongsTestCase(KBForumTestCase):
    """
    Mixing and matching thread, forum, and post data in URLs should fail.
    """

    def setUp(self):
        super(KBBelongsTestCase, self).setUp()
        self.doc = Document.objects.all()[0]
        self.doc_2 = Document.objects.all()[1]
        self.thread = self.doc.thread_set.filter(is_locked=False)[0]
        self.thread_2 = self.doc.thread_set.filter(is_locked=False)[1]
        self.post = self.thread.post_set.all()[0]
        # Login for testing 403s
        self.client.login(username='admin', password='testpass')

    def test_posts_thread_belongs_to_document(self):
        """Posts view - thread belongs to document."""
        r = get(self.client, 'wiki.discuss.posts',
                args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_reply_thread_belongs_to_document(self):
        """Reply action - thread belongs to document."""
        r = post(self.client, 'wiki.discuss.reply', {},
                 args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_locked_thread_belongs_to_document(self):
        """Lock action - thread belongs to document."""
        r = post(self.client, 'wiki.discuss.lock_thread', {},
                 args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_sticky_thread_belongs_to_document(self):
        """Sticky action - thread belongs to document."""
        r = post(self.client, 'wiki.discuss.sticky_thread', {},
                 args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_edit_thread_belongs_to_document(self):
        """Edit thread action - thread belongs to document."""
        r = get(self.client, 'wiki.discuss.edit_thread',
                args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_delete_thread_belongs_to_document(self):
        """Delete thread action - thread belongs to document."""
        r = get(self.client, 'wiki.discuss.delete_thread',
                args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_edit_post_belongs_to_thread_and_document(self):
        """
        Edit post action - post belongs to thread and thread belongs to
        forum.
        """
        r = get(self.client, 'wiki.discuss.edit_post',
                args=[self.doc_2.slug, self.thread.id, self.post.id])
        eq_(404, r.status_code)

        r = get(self.client, 'wiki.discuss.edit_post',
                args=[self.doc.slug, self.thread_2.id, self.post.id])
        eq_(404, r.status_code)

    def test_delete_post_belongs_to_thread_and_document(self):
        """
        Delete post action - post belongs to thread and thread belongs to
        forum.
        """
        r = get(self.client, 'wiki.discuss.delete_post',
                args=[self.doc_2.slug, self.thread.id, self.post.id])
        eq_(404, r.status_code)

        r = get(self.client, 'wiki.discuss.delete_post',
                args=[self.doc.slug, self.thread_2.id, self.post.id])
        eq_(404, r.status_code)
