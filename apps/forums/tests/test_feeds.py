from nose.tools import eq_

from django.test import client

from forums.feeds import ThreadsFeed, PostsFeed
from forums.models import Forum, Thread
from forums.tests import ForumTestCase


class ForumTestFeedSorting(ForumTestCase):

    def setUp(self):
        super(ForumTestFeedSorting, self).setUp()

        # Warm up the prefixer for reverse()
        client.Client().get('/')

    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        f = Forum.objects.get(pk=1)
        given_ = ThreadsFeed().items(f)[0].id
        exp_ = 4L
        eq_(exp_, given_)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        t = Thread.objects.get(pk=1)
        given_ = PostsFeed().items(t)[0].id
        exp_ = 24L
        eq_(exp_, given_)
