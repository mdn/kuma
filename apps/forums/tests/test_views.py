from mock import patch_object, Mock
from nose.tools import eq_

from django.contrib.auth.models import User

from forums.models import Forum, Thread
from forums.tests import ForumTestCase
from forums.events import NewThreadEvent, NewPostEvent
from sumo.tests import get, post
from funfactory.urlresolvers import reverse


class PostPermissionsTests(ForumTestCase):
    """Test post views permissions."""

    def test_read_without_permission(self):
        """Listing posts without the view_in_forum permission should 404."""
        response = get(self.client, 'forums.posts',
                       args=['restricted-forum', 6])
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


class ThreadAuthorityPermissionsTests(ForumTestCase):
    """Test thread views authority permissions."""

    def test_new_thread_without_view_permission(self):
        """Making a new thread without view permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = post(self.client, 'forums.new_thread',
                        {'title': 'Blahs', 'content': 'Blahs'},
                        args=['restricted-forum'])
        eq_(404, response.status_code)

    def test_new_thread_without_post_permission(self):
        """Making a new thread without post permission should 403."""
        self.client.login(username='jsocol', password='testpass')
        with patch_object(Forum, 'allows_viewing_by', Mock(return_value=True)):
            response = post(self.client, 'forums.new_thread',
                            {'title': 'Blahs', 'content': 'Blahs'},
                            args=['restricted-forum'])
        eq_(403, response.status_code)

    def test_watch_GET_405(self):
        """Watch forum with HTTP GET results in 405."""
        self.client.login(username='rrosario', password='testpass')
        f = Forum.objects.filter()[0]
        response = get(self.client, 'forums.watch_forum', args=[f.id])
        eq_(405, response.status_code)

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


class ThreadTests(ForumTestCase):
    """Test thread views."""

    def test_watch_forum(self):
        """Watch then unwatch a forum."""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')

        f = Forum.objects.filter()[0]
        post(self.client, 'forums.watch_forum', {'watch': 'yes'},
             args=[f.slug])
        assert NewThreadEvent.is_notifying(user, f)
        # NewPostEvent is not notifying.
        assert not NewPostEvent.is_notifying(user, f.last_post)

        post(self.client, 'forums.watch_forum', {'watch': 'no'},
             args=[f.slug])
        assert not NewThreadEvent.is_notifying(user, f)

    def test_watch_thread(self):
        """Watch then unwatch a thread."""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')

        t = Thread.objects.filter()[1]
        post(self.client, 'forums.watch_thread', {'watch': 'yes'},
             args=[t.forum.slug, t.id])
        assert NewPostEvent.is_notifying(user, t)
        # NewThreadEvent is not notifying.
        assert not NewThreadEvent.is_notifying(user, t.forum)

        post(self.client, 'forums.watch_thread', {'watch': 'no'},
             args=[t.forum.slug, t.id])
        assert not NewPostEvent.is_notifying(user, t)

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


class ThreadPermissionsTests(ForumTestCase):

    def setUp(self):
        super(ThreadPermissionsTests, self).setUp()
        self.forum = Forum.objects.all()[0]
        admin = User.objects.get(pk=1)
        self.thread = self.forum.thread_set.filter(creator=admin)[0]
        self.post = self.thread.post_set.all()[0]
        # Login for testing 403s
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        self.client.logout()
        super(ThreadPermissionsTests, self).tearDown()

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
