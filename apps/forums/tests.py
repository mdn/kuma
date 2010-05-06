from nose.tools import eq_

from django.test import TestCase

from forums.models import Thread, Post
from forums.views import sort_threads


class ForumsTestCase(TestCase):
    fixtures = ['posts.json']

    def setUp(self):
        """Our fixtures have nulled foreign keys to allow them to be
        installed. This will set them to the correct values."""

        t1 = Thread.objects.get(pk=1)
        t1.last_post = Post.objects.get(pk=1)
        t1.save()

        t2 = Thread.objects.get(pk=2)
        t2.last_post = Post.objects.get(pk=3)
        t2.save()

        t3 = Thread.objects.get(pk=3)
        t3.last_post = Post.objects.get(pk=5)
        t3.save()

    def test_new_post_updates_thread(self):
        """Saving a new post in a thread should update the last_post key in
        that thread to point to the new post."""
        t = Thread.objects.get(pk=1)
        post = t.post_set.create(author=t.creator,
                                 content='an update')
        post.save()
        eq_(post.id, t.last_post_id)

    def test_update_post_does_not_update_thread(self):
        """Updating/saving an old post in a thread should _not_ update the
        last_post key in that thread."""
        p = Post.objects.get(pk=1)
        old = p.thread.last_post_id
        p.content = 'updated content'
        p.save()
        eq_(old, p.thread.last_post_id)

    def test_replies_count(self):
        """The Thread.replies value should remain one less than the number of
        posts in the thread."""
        t = Thread.objects.get(pk=1)
        old = t.replies
        t.post_set.create(author=t.creator, content='test').save()
        eq_(old + 1, t.replies)

    def test_sticky_threads_first(self):
        """Sticky threads should come before non-sticky threads."""
        thread = Thread.objects.all()[0]
        # Thread 2 is the only sticky thread.
        eq_(2, thread.id)

    def test_thread_sorting(self):
        """After the sticky threads, threads should be sorted by the created
        date of the last post."""
        threads = Thread.objects.filter(is_sticky=False)
        self.assert_(threads[0].last_post.created >
                     threads[1].last_post.created)

    def test_post_sorting(self):
        """Posts should be sorted chronologically."""
        posts = Thread.objects.get(pk=1).post_set.all()
        for i in range(len(posts) - 1):
            self.assert_(posts[i].created <= posts[i + 1].created)

    def test_sorting_creator(self):
        """Sorting threads by creator."""
        threads = sort_threads(Thread.objects, 3, 1)
        self.assert_(threads[0].creator.username >=
                     threads[1].creator.username)

    def test_sorting_replies(self):
        """Sorting threads by replies."""
        threads = sort_threads(Thread.objects, 4)
        self.assert_(threads[0].replies <= threads[1].replies)

    def test_sorting_last_post_desc(self):
        """Sorting threads by last_post descendingly."""
        threads = sort_threads(Thread.objects, 5, 1)
        self.assert_(threads[0].last_post.created >=
                     threads[1].last_post.created)
