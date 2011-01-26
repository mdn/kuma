from nose.tools import eq_

from django.contrib.auth.models import User

from kbforums.models import Thread
from kbforums.tests import KBForumTestCase
from kbforums.events import NewThreadEvent, NewPostEvent
from sumo.tests import get, post
from sumo.urlresolvers import reverse
from wiki.models import Document


class ThreadAuthorityPermissionsTests(KBForumTestCase):
    """Test thread views authority permissions."""

    def test_new_thread_without_view_permission(self):
        """Making a new thread without view permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = post(self.client, 'wiki.discuss.new_thread',
                        {'title': 'Blahs', 'content': 'Blahs'},
                        args=['restricted-forum'])
        eq_(404, response.status_code)

    def test_watch_GET_405(self):
        """Watch forum with HTTP GET results in 405."""
        self.client.login(username='rrosario', password='testpass')
        d = Document.objects.filter()[0]
        response = get(self.client, 'wiki.discuss.watch_forum', args=[d.slug])
        eq_(405, response.status_code)

    def test_watch_forum_without_permission(self):
        """Watching forums without the view_in_forum permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = self.client.post(reverse('wiki.discuss.watch_forum',
                                            args=['restricted-forum']),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_watch_thread_without_permission(self):
        """Watching threads without the view_in_forum permission should 404."""
        self.client.login(username='jsocol', password='testpass')
        response = self.client.post(reverse('wiki.discuss.watch_thread',
                                            args=['restricted-forum', 6]),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_read_without_permission(self):
        """Listing threads without the view_in_forum permission should 404."""
        response = get(self.client, 'wiki.discuss.threads',
                       args=['restricted-forum'])
        eq_(404, response.status_code)


class ThreadTests(KBForumTestCase):
    """Test thread views."""

    def test_watch_forum(self):
        """Watch then unwatch a forum."""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')

        d = Document.objects.filter()[0]
        post(self.client, 'wiki.discuss.watch_forum', {'watch': 'yes'},
             args=[d.slug])
        assert NewThreadEvent.is_notifying(user, d)
        # NewPostEvent is not notifying.
        p = d.thread_set.all()[0].post_set.all()[0]
        assert not NewPostEvent.is_notifying(user, p)

        post(self.client, 'wiki.discuss.watch_forum', {'watch': 'no'},
             args=[d.slug])
        assert not NewThreadEvent.is_notifying(user, d)

    def test_watch_thread(self):
        """Watch then unwatch a thread."""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')

        t = Thread.objects.filter()[0]
        post(self.client, 'wiki.discuss.watch_thread', {'watch': 'yes'},
             args=[t.document.slug, t.id])
        assert NewPostEvent.is_notifying(user, t)
        # NewThreadEvent is not notifying.
        assert not NewThreadEvent.is_notifying(user, t.document)

        post(self.client, 'wiki.discuss.watch_thread', {'watch': 'no'},
             args=[t.document.slug, t.id])
        assert not NewPostEvent.is_notifying(user, t)

    def test_edit_thread(self):
        """Changing thread title works."""
        self.client.login(username='jsocol', password='testpass')

        d = Document.objects.filter()[0]
        t_creator = User.objects.get(username='jsocol')
        t = d.thread_set.filter(creator=t_creator)[0]
        post(self.client, 'wiki.discuss.edit_thread', {'title': 'A new title'},
             args=[d.slug, t.id])
        edited_t = d.thread_set.get(pk=t.id)

        eq_('Sticky Thread', t.title)
        eq_('A new title', edited_t.title)

    def test_edit_thread_moderator(self):
        """Editing post as a moderator works."""
        self.client.login(username='pcraciunoiu', password='testpass')

        t = Thread.objects.get(pk=2)
        d = t.document

        eq_('Sticky Thread', t.title)

        r = post(self.client, 'wiki.discuss.edit_thread',
                 {'title': 'new title'}, args=[d.slug, t.id])
        eq_(200, r.status_code)

        edited_t = Thread.uncached.get(pk=2)
        eq_('new title', edited_t.title)


class ThreadPermissionsTests(KBForumTestCase):

    def setUp(self):
        super(ThreadPermissionsTests, self).setUp()
        self.doc = Document.objects.all()[0]
        admin = User.objects.get(pk=1)
        self.thread = self.doc.thread_set.filter(creator=admin)[0]
        self.post = self.thread.post_set.all()[0]
        # Login for testing 403s
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        self.client.logout()
        super(ThreadPermissionsTests, self).tearDown()

    def test_edit_thread_403(self):
        """Editing a thread without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.edit_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_edit_locked_thread_403(self):
        """Editing a locked thread returns 403."""
        jsocol = User.objects.get(username='jsocol')
        t = self.doc.thread_set.filter(creator=jsocol, is_locked=True)[0]
        response = get(self.client, 'wiki.discuss.edit_thread',
                       args=[self.doc.slug, t.id])
        eq_(403, response.status_code)

    def test_delete_thread_403(self):
        """Deleting a thread without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.delete_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_sticky_thread_405(self):
        """Marking a thread sticky with a HTTP GET returns 405."""
        response = get(self.client, 'wiki.discuss.sticky_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(405, response.status_code)

    def test_sticky_thread_403(self):
        """Marking a thread sticky without permissions returns 403."""
        response = post(self.client, 'wiki.discuss.sticky_thread',
                        args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_locked_thread_403(self):
        """Marking a thread locked without permissions returns 403."""
        response = post(self.client, 'wiki.discuss.lock_thread',
                        args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_locked_thread_405(self):
        """Marking a thread locked via a GET instead of a POST request."""
        response = get(self.client, 'wiki.discuss.lock_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(405, response.status_code)

    def test_post_edit_403(self):
        """Editing a post without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.edit_post',
                       args=[self.doc.slug, self.thread.id, self.post.id])
        eq_(403, response.status_code)

    def test_post_delete_403(self):
        """Deleting a post without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.delete_post',
                       args=[self.doc.slug, self.thread.id, self.post.id])
        eq_(403, response.status_code)
