from django.test import TestCase

from forums.models import Thread, Post


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
        pass

    def test_update_post_does_not_update_thread(self):
        """Updating/saving an old post in a thread should _not_ update the
        last_post key in that thread."""
        pass

    def test_replies_count(self):
        """The Thread.replies value should be one less than the number of
        posts in the thread."""
        pass

    def test_sticky_threads_first(self):
        """Sticky threads should come before non-sticky threads."""
        thread = Thread.objects.all()[0]
        # Thread 2 is the only sticky thread.
        self.assertEquals(2, thread.id)
