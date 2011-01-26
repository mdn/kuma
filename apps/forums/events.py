import itertools

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from tower import ugettext as _

from notifications.events import InstanceEvent
from forums.models import Thread, Forum


class ThreadReplyEvent(InstanceEvent):
    """An event which fires when a thread receives a reply"""

    event_type = 'thread reply'
    content_type = Thread

    def __init__(self, reply):
        super(ThreadReplyEvent, self).__init__(reply.thread)
        # Need to store the reply for _mails
        self.reply = reply

    def _mails(self, users_and_watches):
        subject = _('Reply to: %s') % self.reply.thread.title
        t = loader.get_template('forums/email/new_post.ltxt')
        c = {'post': self.reply.content, 'author': self.reply.author.username,
             'host': Site.objects.get_current().domain,
             'thread_title': self.instance.title,
             'post_url': self.reply.get_absolute_url()}
        content = t.render(Context(c))
        return (EmailMessage(subject, content,
                             settings.NOTIFICATIONS_FROM_ADDRESS,
                             [u.email]) for
                u, _ in users_and_watches)

    def users_watching(self):
        """Return users watching thread replies OR forum posts."""
        thread_watchers = self._users_watching_by_filter(
            object_id=self.instance.pk)
        forum_watchers = ForumThreadEvent(self.reply).users_watching()
        return set(itertools.chain(thread_watchers, forum_watchers))


class ForumThreadEvent(InstanceEvent):
    """An event which fires when a new thread is added to a forum"""

    event_type = 'forum thread'
    content_type = Forum

    def __init__(self, post):
        super(ForumThreadEvent, self).__init__(post.thread.forum)
        # Need to store the post for _mails
        self.post = post

    def _mails(self, users_and_watches):
        subject = _('New thread in %s forum: %s') % (
            self.post.thread.forum.name, self.post.thread.title)
        t = loader.get_template('forums/email/new_thread.ltxt')
        c = {'post': self.post.content, 'author': self.post.author.username,
             'host': Site.objects.get_current().domain,
             'thread_title': self.post.thread.title,
             'post_url': self.post.thread.get_absolute_url()}
        content = t.render(Context(c))

        return (EmailMessage(subject, content,
                             settings.NOTIFICATIONS_FROM_ADDRESS,
                             [u.email]) for
                u, _ in users_and_watches)
