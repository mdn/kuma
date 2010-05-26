from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from forums.models import Forum
from forums.tests import ForumTestCase


class ThreadsTemplateTestCase(ForumTestCase):

    def test_last_thread_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        forum = Forum.objects.filter()[0]
        response = self.client.get(reverse('forums.threads',
                                           args=[forum.slug]), follow=True)
        doc = pq(response.content)
        last_post_link = doc('ol.threads div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-3')


class ForumsTemplateTestCase(ForumTestCase):
    fixtures = ['users.json', 'posts.json']

    def setUp(self):
        super(ForumsTemplateTestCase, self).setUp()
        self.forum = Forum.objects.all()[0]
        self.thread = self.forum.thread_set.all()[0]
        self.post = self.thread.post_set.all()[0]
        # Login for testing 403s
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        super(ForumsTemplateTestCase, self).tearDown()
        self.client.logout()

    def test_last_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        response = self.client.get(reverse('forums.forums'), follow=True)
        doc = pq(response.content)
        last_post_link = doc('ol.forums div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-24')

    def test_edit_thread_403(self):
        """Editing a thread without permissions returns 403."""
        response = self.client.get(
            reverse('forums.edit_thread',
                    args=[self.forum.slug, self.thread.id]),
            follow=True)
        eq_(403, response.status_code)

    def test_delete_thread_403(self):
        """Deleting a thread without permissions returns 403."""
        response = self.client.get(
            reverse('forums.delete_thread',
                    args=[self.forum.slug, self.thread.id]),
            follow=True)
        eq_(403, response.status_code)

    def test_sticky_thread_403(self):
        """Marking a thread sticky without permissions returns 403."""
        response = self.client.get(
            reverse('forums.sticky_thread',
                    args=[self.forum.slug, self.thread.id]),
            follow=True)
        eq_(403, response.status_code)

    def test_locked_thread_403(self):
        """Marking a thread locked without permissions returns 403."""
        response = self.client.post(
            reverse('forums.lock_thread',
                    args=[self.forum.slug, self.thread.id]),
            follow=True)
        eq_(403, response.status_code)

    def test_locked_thread_405(self):
        """Marking a thread locked via a GET instead of a POST request."""
        response = self.client.get(
            reverse('forums.lock_thread',
                    args=[self.forum.slug, self.thread.id]),
            follow=True)
        eq_(405, response.status_code)        

    def test_post_edit_403(self):
        """Editing a post without permissions returns 403."""
        response = self.client.get(
            reverse('forums.edit_post',
                    args=[self.forum.slug, self.thread.id, self.post.id]),
            follow=True)
        eq_(403, response.status_code)

    def test_post_delete_403(self):
        """Deleting a post without permissions returns 403."""
        response = self.client.get(
            reverse('forums.delete_post',
                    args=[self.forum.slug, self.thread.id, self.post.id]),
            follow=True)
        eq_(403, response.status_code)


class PostsTemplateTestCase(ForumTestCase):

    def test_long_title_truncated_in_crumbs(self):
        """A very long thread title gets truncated in the breadcrumbs"""
        forum = Forum.objects.filter()[0]
        response = self.client.get(reverse('forums.posts',
                                           args=[forum.slug, 4]), follow=True)
        doc = pq(response.content)
        crumb = doc('ol.breadcrumbs li:last-child')
        eq_(crumb.text(), 'A thread with a very very ...')
