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
        f = Forum.objects.get(pk=1)
        given_ = ThreadsFeed().items(f)[0].id
        exp_ = 3L
        eq_(exp_, given_)

    def test_posts_sort(self):
        t = Thread.objects.get(pk=1)
        given_ = PostsFeed().items(t)[0].id
        exp_ = 24L
        eq_(exp_, given_)
