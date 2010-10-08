from nose.tools import eq_
from pyquery import PyQuery as pq

from kbforums.feeds import ThreadsFeed, PostsFeed
from kbforums.models import Thread
from kbforums.tests import KBForumTestCase, get
from wiki.models import Document


class FeedSortingTestCase(KBForumTestCase):

    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        f = Document.objects.get(pk=1)
        given_ = ThreadsFeed().items(f)[0].id
        exp_ = 4L
        eq_(exp_, given_)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        t = Thread.objects.get(pk=1)
        given_ = PostsFeed().items(t)[0].id
        exp_ = 24L
        eq_(exp_, given_)

    def test_multi_feed_titling(self):
        """Ensure that titles are being applied properly to feeds."""
        d = Document.objects.filter()[0]
        response = get(self.client, 'wiki.discuss.threads', args=[d.slug])
        doc = pq(response.content)
        given_ = doc('link[type="application/atom+xml"]')[0].attrib['title']
        exp_ = ThreadsFeed().title(d)
        eq_(exp_, given_)
