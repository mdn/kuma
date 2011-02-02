from nose.tools import eq_
from pyquery import PyQuery as pq

from django.contrib.auth.models import User

from forums.models import Forum, Thread, Post
from forums.tests import ForumTestCase
from sumo.tests import get, post


class PostsTemplateTests(ForumTestCase):

    def test_empty_reply_errors(self):
        """Posting an empty reply shows errors."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        t = f.thread_set.all()[0]
        response = post(self.client, 'forums.reply', {'content': ''},
                        args=[f.slug, t.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Please provide a message.')

    def test_edit_post_errors(self):
        """Changing post content works."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        t = f.thread_set.all()[0]
        p_author = User.objects.get(username='jsocol')
        p = t.post_set.filter(author=p_author)[0]
        response = post(self.client, 'forums.edit_post',
                        {'content': 'wha?'}, args=[f.slug, t.id, p.id])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text,
            'Your message is too short (4 characters). ' +
            'It must be at least 5 characters.')

    def test_edit_thread_template(self):
        """The edit-post template should render."""
        self.client.login(username='jsocol', password='testpass')

        u = User.objects.get(username='jsocol')
        p = Post.objects.filter(author=u, thread__is_locked=False)[0]
        res = get(self.client, 'forums.edit_post',
                 args=[p.thread.forum.slug, p.thread.id, p.id])

        doc = pq(res.content)
        eq_(len(doc('form.edit-post')), 1)

    def test_edit_post(self):
        """Changing post content works."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        t = f.thread_set.all()[0]
        p_author = User.objects.get(username='jsocol')
        p = t.post_set.filter(author=p_author)[0]
        post(self.client, 'forums.edit_post', {'content': 'Some new content'},
             args=[f.slug, t.id, p.id])
        edited_p = t.post_set.get(pk=p.id)

        eq_('Some new content', edited_p.content)

    def test_long_title_truncated_in_crumbs(self):
        """A very long thread title gets truncated in the breadcrumbs"""
        forum = Forum.objects.filter()[0]
        response = get(self.client, 'forums.posts', args=[forum.slug, 4])
        doc = pq(response.content)
        crumb = doc('ol.breadcrumbs li:last-child')
        eq_(crumb.text(), 'A thread with a very very ...')

    def test_edit_post_moderator(self):
        """Editing post as a moderator works."""
        self.client.login(username='pcraciunoiu', password='testpass')

        p = Post.objects.get(pk=4)
        t = p.thread
        f = t.forum

        r = post(self.client, 'forums.edit_post',
                 {'content': 'More new content'}, args=[f.slug, t.id, p.id])
        eq_(200, r.status_code)

        edited_p = Post.uncached.get(pk=p.pk)
        eq_('More new content', edited_p.content)

    def test_preview_reply(self):
        """Preview a reply."""
        self.client.login(username='rrosario', password='testpass')
        f = Forum.objects.filter()[0]
        t = f.thread_set.all()[0]
        num_posts = t.post_set.count()
        content = 'Full of awesome.'
        response = post(self.client, 'forums.reply',
                        {'content': content, 'preview': 'any string'},
                        args=[f.slug, t.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc('#post-preview div.content').text())
        eq_(num_posts, t.post_set.count())

    def test_watch_thread(self):
        """Watch and unwatch a thread."""
        self.client.login(username='rrosario', password='testpass')

        t = Thread.objects.filter()[1]
        response = post(self.client, 'forums.watch_thread', {'watch': 'yes'},
                        args=[t.forum.slug, t.id])
        self.assertContains(response, 'Watching')

        response = post(self.client, 'forums.watch_thread', {'watch': 'no'},
                        args=[t.forum.slug, t.id])
        self.assertNotContains(response, 'Watching')


class ThreadsTemplateTests(ForumTestCase):

    def test_last_thread_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        response = get(self.client, 'forums.threads', args=['test-forum'])
        doc = pq(response.content)
        last_post_link = doc('ol.threads div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-4')

    def test_empty_thread_errors(self):
        """Posting an empty thread shows errors."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        response = post(self.client, 'forums.new_thread',
                        {'title': '', 'content': ''}, args=[f.slug])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text, 'Please provide a title.')
        eq_(errors[1].text, 'Please provide a message.')

    def test_new_short_thread_errors(self):
        """Posting a short new thread shows errors."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        response = post(self.client, 'forums.new_thread',
                        {'title': 'wha?', 'content': 'wha?'}, args=[f.slug])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text,
            'Your title is too short (4 characters). ' +
            'It must be at least 5 characters.')
        eq_(errors[1].text,
            'Your message is too short (4 characters). ' +
            'It must be at least 5 characters.')

    def test_edit_thread_errors(self):
        """Editing thread with too short of a title shows errors."""
        self.client.login(username='jsocol', password='testpass')

        f = Forum.objects.filter()[0]
        t_creator = User.objects.get(username='jsocol')
        t = f.thread_set.filter(creator=t_creator)[0]
        response = post(self.client, 'forums.edit_thread',
                        {'title': 'wha?'}, args=[f.slug, t.id])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text,
            'Your title is too short (4 characters). ' +
            'It must be at least 5 characters.')

    def test_edit_thread_template(self):
        """The edit-thread template should render."""
        self.client.login(username='jsocol', password='testpass')

        u = User.objects.get(username='jsocol')
        t = Thread.objects.filter(creator=u, is_locked=False)[0]
        res = get(self.client, 'forums.edit_thread',
                 args=[t.forum.slug, t.id])

        doc = pq(res.content)
        eq_(len(doc('form.edit-thread')), 1)

    def test_watch_forum(self):
        """Watch and unwatch a forum."""
        self.client.login(username='rrosario', password='testpass')

        f = Forum.objects.filter()[0]
        response = post(self.client, 'forums.watch_forum', {'watch': 'yes'},
                        args=[f.slug])
        self.assertContains(response, 'Watching')

        response = post(self.client, 'forums.watch_forum', {'watch': 'no'},
                        args=[f.slug])
        self.assertNotContains(response, 'Watching')


class ForumsTemplateTests(ForumTestCase):

    def setUp(self):
        super(ForumsTemplateTests, self).setUp()
        self.forum = Forum.objects.all()[0]
        admin = User.objects.get(pk=1)
        self.thread = self.forum.thread_set.filter(creator=admin)[0]
        self.post = self.thread.post_set.all()[0]
        # Login for testing 403s
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        self.client.logout()
        super(ForumsTemplateTests, self).tearDown()

    def test_last_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        response = get(self.client, 'forums.forums')
        doc = pq(response.content)
        last_post_link = doc('ol.forums div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-25')

    def test_restricted_is_invisible(self):
        """Forums with restricted view_in permission shouldn't show up."""
        response = get(self.client, 'forums.forums')
        self.assertNotContains(response, 'restricted-forum')


class NewThreadTemplateTests(ForumTestCase):

    def test_preview(self):
        """Preview the thread post."""
        self.client.login(username='rrosario', password='testpass')
        f = Forum.objects.filter()[0]
        num_threads = f.thread_set.count()
        content = 'Full of awesome.'
        response = post(self.client, 'forums.new_thread',
                        {'title': 'Topic', 'content': content,
                         'preview': 'any string'}, args=[f.slug])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc('#post-preview div.content').text())
        eq_(num_threads, f.thread_set.count())
