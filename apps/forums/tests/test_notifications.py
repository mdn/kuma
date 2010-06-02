from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

import mock

from forums.tasks import build_notification
import notifications.tasks
from . import ForumTestCase
from forums.models import Post, Thread


EMAIL_CONTENT = (
    u"""

Reply to thread: Not a sticky thread

User jsocol has replied to a thread you're watching. Here
is their reply:

========

A post in a non-sticky thread

========

To view this post on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/forums/test-forum/3#post-5

""",
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

""",)


class NotificationTestCase(ForumTestCase):
    """Test that notifications get sent."""

    def setUp(self):
        super(NotificationTestCase, self).setUp()

        self.ct = ContentType.objects.get_for_model(Thread).pk

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_notification(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        post = Post.objects.get(pk=5)
        build_notification(post)

        delay.assert_called_with(
            self.ct, post.thread.id,
            u'Reply to: Not a sticky thread',
            EMAIL_CONTENT[0],
            (u'user118533@nowhere',))

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_notification_on_save(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        t = Thread.objects.get(pk=2)
        user = User.objects.get(pk=118533)
        p = t.post_set.create(author=user, content='a post')
        p.save()

        delay.assert_called_with(
            self.ct, t.pk,
            u'Reply to: Sticky Thread',
            EMAIL_CONTENT[1] % p.pk,
            (u'user118533@nowhere',))
