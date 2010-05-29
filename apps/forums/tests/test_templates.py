from nose.tools import eq_
from pyquery import PyQuery as pq

from django.contrib.auth.models import User

from forums.models import Forum
from forums.tests import ForumTestCase, get, post


class PostsTemplateTestCase(ForumTestCase):

    def test_empty_reply_errors(self):
        """Posting an empty reply shows errors."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        t = f.thread_set.all()[0]
        response = post(self.client, 'forums.reply', {'content': ''},
                        args=[f.slug, t.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Content must be longer than 5 characters.')


class ThreadsTemplateTestCase(ForumTestCase):

    def test_last_thread_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        forum = Forum.objects.filter()[0]
        response = get(self.client, 'forums.threads', args=[forum.slug])
        doc = pq(response.content)
        last_post_link = doc('ol.threads div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-3')

    def test_empty_thread_errors(self):
        """Posting an empty thread shows errors."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        response = post(self.client, 'forums.new_thread',
                        {'title': '', 'content': ''}, args=[f.slug])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text, 'Title must be longer than 5 characters.')
        eq_(errors[1].text, 'Content must be longer than 5 characters.')

    def test_edit_thread_errors(self):
        """Editing thread with too short of a title shows errors."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        t_creator = User.objects.get(username='jsocol')
        t = f.thread_set.filter(creator=t_creator)[0]
        response = post(self.client, 'forums.edit_thread',
                        {'title': ''}, args=[f.slug, t.id])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text, 'Title must be longer than 5 characters.')

    def test_edit_thread(self):
        """Changing thread title works."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        t_creator = User.objects.get(username='jsocol')
        t = f.thread_set.filter(creator=t_creator)[0]
        post(self.client, 'forums.edit_thread', {'title': 'A new title'},
             args=[f.slug, t.id])
        edited_t = f.thread_set.get(pk=t.id)

        eq_('Sticky Thread', t.title)
        eq_('A new title', edited_t.title)


class ForumsTemplateTestCase(ForumTestCase):

    def setUp(self):
        super(ForumsTemplateTestCase, self).setUp()
        self.forum = Forum.objects.all()[0]
        admin = User.objects.get(pk=1)
        self.thread = self.forum.thread_set.filter(creator=admin)[0]
        self.post = self.thread.post_set.all()[0]
        # Login for testing 403s
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        super(ForumsTemplateTestCase, self).tearDown()
        self.client.logout()

    def test_last_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        response = get(self.client, 'forums.forums')
        doc = pq(response.content)
        last_post_link = doc('ol.forums div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-25')

    def test_edit_thread_403(self):
        """Editing a thread without permissions returns 403."""
        response = get(self.client, 'forums.edit_thread',
                       args=[self.forum.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_delete_thread_403(self):
        """Deleting a thread without permissions returns 403."""
        response = get(self.client, 'forums.delete_thread',
                       args=[self.forum.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_sticky_thread_405(self):
        """Marking a thread sticky with a HTTP GET returns 405."""
        response = get(self.client, 'forums.sticky_thread',
                       args=[self.forum.slug, self.thread.id])
        eq_(405, response.status_code)

    def test_sticky_thread_403(self):
        """Marking a thread sticky without permissions returns 403."""
        response = post(self.client, 'forums.sticky_thread',
                        args=[self.forum.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_locked_thread_403(self):
        """Marking a thread locked without permissions returns 403."""
        response = post(self.client, 'forums.lock_thread',
                        args=[self.forum.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_locked_thread_405(self):
        """Marking a thread locked via a GET instead of a POST request."""
        response = get(self.client, 'forums.lock_thread',
                       args=[self.forum.slug, self.thread.id])
        eq_(405, response.status_code)

    def test_post_edit_403(self):
        """Editing a post without permissions returns 403."""
        response = get(self.client, 'forums.edit_post',
                       args=[self.forum.slug, self.thread.id, self.post.id])
        eq_(403, response.status_code)

    def test_post_delete_403(self):
        """Deleting a post without permissions returns 403."""
        response = get(self.client, 'forums.delete_post',
                       args=[self.forum.slug, self.thread.id, self.post.id])
        eq_(403, response.status_code)

        doc = pq(response.content)
        eq_('Access denied', doc('#content-inner h2').text())


class PostsTemplateTestCase(ForumTestCase):

    def test_long_title_truncated_in_crumbs(self):
        """A very long thread title gets truncated in the breadcrumbs"""
        forum = Forum.objects.filter()[0]
        response = get(self.client, 'forums.posts', args=[forum.slug, 4])
        doc = pq(response.content)
        crumb = doc('ol.breadcrumbs li:last-child')
        eq_(crumb.text(), 'A thread with a very very ...')
