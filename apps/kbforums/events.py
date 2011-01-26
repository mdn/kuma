from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from tower import ugettext as _

from kbforums.models import Thread
from notifications.events import InstanceEvent, EventUnion
from wiki.models import Document


class NewPostEvent(InstanceEvent):
    """An event which fires when a thread receives a reply"""

    event_type = 'kbthread reply'
    content_type = Thread

    def __init__(self, reply):
        super(NewPostEvent, self).__init__(reply.thread)
        # Need to store the reply for _mails
        self.reply = reply

    def fire(self, **kwargs):
        """Notify not only watchers of this thread but of the parent forum."""
        return EventUnion(self, NewThreadEvent(self.reply)).fire(**kwargs)

    def _mails(self, users_and_watches):
        subject = _('Reply to: %s') % self.reply.thread.title
        t = loader.get_template('kbforums/email/new_post.ltxt')
        c = {'post': self.reply.content, 'author': self.reply.creator.username,
             'host': Site.objects.get_current().domain,
             'thread_title': self.instance.title,
             'post_url': self.reply.get_absolute_url()}
        content = t.render(Context(c))
        return (EmailMessage(subject, content,
                             settings.NOTIFICATIONS_FROM_ADDRESS,
                             [u.email]) for
                u, dummy in users_and_watches)


class NewThreadEvent(InstanceEvent):
    """An event which fires when a new thread is added to a kbforum"""

    event_type = 'kbforum thread'
    content_type = Document

    def __init__(self, post):
        super(NewThreadEvent, self).__init__(post.thread.document)
        # Need to store the post for _mails
        self.post = post

    def _mails(self, users_and_watches):
        subject = _('New thread in %s forum: %s') % (
            self.post.thread.document.title, self.post.thread.title)
        t = loader.get_template('kbforums/email/new_thread.ltxt')
        c = {'post': self.post.content, 'author': self.post.creator.username,
             'host': Site.objects.get_current().domain,
             'thread_title': self.post.thread.title,
             'post_url': self.post.thread.get_absolute_url()}
        content = t.render(Context(c))

        return (EmailMessage(subject, content,
                             settings.NOTIFICATIONS_FROM_ADDRESS,
                             [u.email]) for
                u, dummy in users_and_watches)
