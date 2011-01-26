from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose import SkipTest
from nose.tools import eq_

from forums.events import ThreadReplyEvent, ForumThreadEvent
from forums.models import Thread, Forum, Post
from forums.tests import ForumTestCase
from sumo.tests import post


# Some of these contain a locale prefix on included links, while others don't.
# This depends on whether the tests use them inside or outside the scope of a
# request. See the long explanation in questions.tests.test_notifications.
EMAIL_CONTENT = (
    u"""

Reply to thread: Sticky Thread

User jsocol has replied to a thread you're watching. Here
is their reply:

========

a post

========

To view this post on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/forums/test-forum/2#post-%s
""",
    u"""

New thread: a title

User jsocol has posted a new thread in a forum you're watching.
Here is the thread:

========

a post

========

To view this post on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/forums/test-forum/%s
""",)


class NotificationsTests(ForumTestCase):
    """Test that notifications get sent."""

    @mock.patch_object(ThreadReplyEvent, 'fire')
    def test_fire_on_reply(self, fire):
        """The event fires when there is a reply."""
        t = Thread.objects.get(pk=2)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t.forum.slug, t.id])
        # ThreadReplyEvent.fire() is called.
        assert fire.called

    @mock.patch_object(ForumThreadEvent, 'fire')
    def test_fire_on_new_thread(self, fire):
        """The event fires when there is a new thread."""
        f = Forum.objects.get(pk=1)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.new_thread',
             {'title': 'a title', 'content': 'a post'},
             args=[f.slug])
        # Event.fire() is called.
        assert fire.called

    def _test_watch_then_post(self, event_cls,
                               cls_created, obj,
                               post_path, post_data, post_args, subject,
                               watch_path, watch_args=None):
        """The event fires and sends emails when watching a thread."""
        email_id = 0 if cls_created == Post else 1
        watch_args = watch_args or post_args
        # Watch this object.
        self.client.login(username='jsocol', password='testpass')
        user = User.objects.get(username='jsocol')
        post(self.client, watch_path, {'watch': 'yes'}, args=watch_args)
        # Watch exists.
        assert event_cls.is_notifying(user, obj), (
               '%s should be notifying.' % str(event_cls))

        # Then act on it.
        post(self.client, post_path, post_data, args=post_args)
        # Fetch created object.
        item_created = cls_created.objects.all().order_by('-id')[0]

        # An email is sent out.
        # TODO: A user shouldn't be notified of his own change.
        eq_(1, len(mail.outbox))
        eq_(mail.outbox[0].to, ['user118533@nowhere'])
        eq_(mail.outbox[0].subject, subject)
        eq_(mail.outbox[0].body, EMAIL_CONTENT[email_id] % item_created.pk)

        # Then remove the watch.
        post(self.client, watch_path, args=watch_args)
        # Watch no longer exists.
        assert not event_cls.is_notifying(user, obj), (
               '%s should be notifying.' % str(event_cls))

    @mock.patch_object(Site.objects, 'get_current')
    def test_watch_thread_then_reply(self, get_current):
        """The event fires and sends emails when watching a thread."""
        get_current.return_value.domain = 'testserver'

        t = Thread.objects.get(pk=2)
        self._test_watch_then_post(
            ThreadReplyEvent, Post, t,
            'forums.reply', {'content': 'a post'}, [t.forum.slug, t.id],
            'Reply to: Sticky Thread', 'forums.watch_thread')

    @mock.patch_object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread(self, get_current):
        """Watching a forum and creating a new thread should send email."""
        get_current.return_value.domain = 'testserver'

        f = Forum.objects.get(pk=1)
        self._test_watch_then_post(
            ForumThreadEvent, Thread, f,
            'forums.new_thread', {'title': 'a title', 'content': 'a post'},
            [f.slug], 'New thread in Test forum forum: a title',
            'forums.watch_forum')

    @mock.patch_object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post(self, get_current):
        """Watching a forum and replying to a thread should send email."""
        get_current.return_value.domain = 'testserver'

        f = Forum.objects.get(pk=1)
        t = f.thread_set.all()[0]
        self._test_watch_then_post(
            ForumThreadEvent, Post, f,
            'forums.reply', {'content': 'a post'},
            [f.slug, t.id], 'Reply to: Sticky Thread',
            'forums.watch_forum', [f.slug])

    @mock.patch_object(Site.objects, 'get_current')
    def test_watch_both_then_new_post(self, get_current):
        """Watching both and replying to a thread should send ONE email."""
        # TODO: Make this work after unique-fying list of user-watch pairs.
        raise SkipTest
        get_current.return_value.domain = 'testserver'

        f = Forum.objects.get(pk=1)
        t = f.thread_set.all()[0]
        # Watch this forum.
        self.client.login(username='jsocol', password='testpass')
        user = User.objects.get(username='jsocol')
        post(self.client, 'forums.watch_forum', {'watch': 'yes'},
             args=[f.slug])
        assert ForumThreadEvent.is_notifying(user, f), (
               'ForumThreadEvent should be notifying.')
        assert not ThreadReplyEvent.is_notifying(user, f), (
               'ThreadReplyEvent should not be notifying.')
        # Watch this thread.
        post(self.client, 'forums.watch_thread', {'watch': 'yes'},
             args=[t.forum.slug, t.id])
        # Watches exist.
        assert ThreadReplyEvent.is_notifying(user, f), (
               'ThreadReplyEvent should be notifying.')

        # Then reply to it.
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t.forum.slug, t.id])
        # Fetch forum again.
        f = Forum.uncached.get(pk=1)
        t = f.thread_set.all()[0]

        # An email is sent out.
        # TODO: A user shouldn't be notified of his own change.
        eq_(1, len(mail.outbox))
        eq_(mail.outbox[0].to, ['user118533@nowhere'])
        eq_(mail.outbox[0].subject, 'Reply to: Sticky Thread')
        eq_(mail.outbox[0].body, EMAIL_CONTENT[0] % t.last_post.pk)

        # Then remove the watches.
        post(self.client, 'forums.watch_forum', args=[f.slug])
        assert not ForumThreadEvent.is_notifying(user, f), (
               'ForumThreadEvent should not be notifying.')
        assert ThreadReplyEvent.is_notifying(user, f), (
               'ThreadReplyEvent should be notifying.')
        post(self.client, 'forums.watch_thread', args=[f.slug, t.id])
        assert not ThreadReplyEvent.is_notifying(user, f), (
               'ThreadReplyEvent should not be notifying.')
