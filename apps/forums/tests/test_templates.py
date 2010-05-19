from nose.tools import eq_
from pyquery import PyQuery as pq

from forums.models import Forum
from sumo.urlresolvers import reverse
from forums.tests import ForumTestCase


class ForumTemplateTestCase(ForumTestCase):

    def test_last_thread_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        forum = Forum.objects.filter()[0]
        response = self.client.get(reverse('forums.threads',
                                           args=[forum.slug]), follow=True)
        doc = pq(response.content)
        last_post_link = doc('ol.threads div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-3')
