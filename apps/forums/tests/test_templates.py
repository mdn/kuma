from mock import patch_object, Mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from django.contrib.auth.models import User

from forums.models import Forum, Thread, Post
from forums.tests import ForumTestCase, get, post
from notifications import check_watch
from sumo.urlresolvers import reverse


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

    def test_read_without_permission(self):
        """Listing posts without the view_in_forum permission should 404."""
        response = get(self.client, 'forums.posts', args=['restricted-forum', 6])
        eq_(404, response.status_code)

    def test_reply_without_view_permission(self):
        """Posting without view_in_forum permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = post(self.client, 'forums.reply', {'content': 'Blahs'},
                        args=['restricted-forum', 6])
        eq_(404, response.status_code)

    def test_reply_without_post_permission(self):
        """Posting without post_in_forum permission should 403."""
        self.client.login(username='jsocol', password='testpass')
        with patch_object(Forum, 'allows_viewing_by', Mock(return_value=True)):
            response = post(self.client, 'forums.reply', {'content': 'Blahs'},
                            args=['restricted-forum', 6])
        eq_(403, response.status_code)


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
        eq_(errors[0].text, 'Please provide a title.')
        eq_(errors[1].text, 'Please provide a message.')

    def test_new_thread_without_view_permission(self):
        """Making a new thread without view permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = post(self.client, 'forums.new_thread',
                        {'title': 'Blahs', 'content': 'Blahs'}, args=['restricted-forum'])
        eq_(404, response.status_code)

    def test_new_thread_without_post_permission(self):
        """Making a new thread without post permission should 403."""
        self.client.login(username='jsocol', password='testpass')
        with patch_object(Forum, 'allows_viewing_by', Mock(return_value=True)):
            response = post(self.client, 'forums.new_thread',
                            {'title': 'Blahs', 'content': 'Blahs'}, args=['restricted-forum'])
        eq_(403, response.status_code)

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

    def test_edit_thread_moderator(self):
        """Editing post as a moderator works."""
        self.client.login(username='pcraciunoiu', password='testpass')

        t = Thread.objects.get(pk=2)
        f = t.forum

        eq_('Sticky Thread', t.title)

        r = post(self.client, 'forums.edit_thread',
                 {'title': 'new title'}, args=[f.slug, t.id])
        eq_(200, r.status_code)

        edited_t = Thread.uncached.get(pk=2)
        eq_('new title', edited_t.title)

    def test_watch_GET_405(self):
        """Watch forum with HTTP GET results in 405."""
        self.client.login(username='rrosario', password='testpass')
        f = Forum.objects.filter()[0]
        response = get(self.client, 'forums.watch_forum', args=[f.id])
        eq_(405, response.status_code)

    def test_watch_forum(self):
        """Watch then unwatch a forum."""
        self.client.login(username='rrosario', password='testpass')
        f = Forum.objects.filter()[0]
        post(self.client, 'forums.watch_forum', {'watch': 'yes'},
             args=[f.slug])
        assert check_watch(Forum, f.id, 'user118577@nowhere',
                           'post'), 'Watch was not created'

        post(self.client, 'forums.watch_forum', {'watch': 'no'},
             args=[f.slug])
        assert not check_watch(Forum, f.id, 'user118577@nowhere',
                           'post'), 'Watch was not created'

    def test_watch_forum_without_permission(self):
        """Watching forums without the view_in_forum permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = self.client.post(reverse('forums.watch_forum',
                                            args=['restricted-forum']),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_watch_thread_without_permission(self):
        """Watching threads without the view_in_forum permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = self.client.post(reverse('forums.watch_thread',
                                            args=['restricted-forum', 6]),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_read_without_permission(self):
        """Listing threads without the view_in_forum permission should 404."""
        response = get(self.client, 'forums.threads',
                       args=['restricted-forum'])
        eq_(404, response.status_code)


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
        self.client.logout()
        super(ForumsTemplateTestCase, self).tearDown()

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

    def test_edit_thread_403(self):
        """Editing a thread without permissions returns 403."""
        response = get(self.client, 'forums.edit_thread',
                       args=[self.forum.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_edit_locked_thread_403(self):
        """Editing a locked thread returns 403."""
        jsocol = User.objects.get(username='jsocol')
        t = self.forum.thread_set.filter(creator=jsocol, is_locked=True)[0]
        response = get(self.client, 'forums.edit_thread',
                       args=[self.forum.slug, t.id])
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

    def test_move_thread_403(self):
        """Moving a thread without permissions returns 403."""
        response = post(self.client, 'forums.move_thread', {'forum': 2},
                        args=[self.forum.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_move_thread_405(self):
        """Moving a thread via a GET instead of a POST request."""
        response = get(self.client, 'forums.move_thread',
                       args=[self.forum.slug, self.thread.id])
        eq_(405, response.status_code)

    def test_move_thread(self):
        """Move a thread."""
        self.client.login(username='rrosario', password='testpass')
        response = post(self.client, 'forums.move_thread',
                        {'forum': 2},
                        args=[self.forum.slug, self.thread.id])
        eq_(200, response.status_code)
        thread = Thread.objects.get(pk=self.thread.pk)
        eq_(2, thread.forum.id)

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
