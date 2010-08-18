from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.template import Context, loader

from celery.decorators import task
from tower import ugettext as _

from notifications.tasks import send_notification


@task
def build_reply_notification(post):
    thread_ct = ContentType.objects.get_for_model(post.thread)
    forum_ct = ContentType.objects.get_for_model(post.thread.forum)

    subject = _('Reply to: %s') % post.thread.title
    t = loader.get_template('forums/email/new_post.ltxt')
    c = {'post': post.content, 'author': post.author.username,
         'host': Site.objects.get_current().domain,
         'thread_title': post.thread.title,
         'post_url': post.get_absolute_url()}
    content = t.render(Context(c))
    exclude = (post.author.email,)

    # Send to thread watchers
    send_notification.delay(thread_ct.id, post.thread.id, subject,
                            content, exclude, 'reply')
    # And forum watchers
    send_notification.delay(forum_ct.id, post.thread.forum.id, subject,
                            content, exclude, 'post')


@task
def build_thread_notification(post):
    forum_ct = ContentType.objects.get_for_model(post.thread.forum)

    subject = _('New thread in %s forum: %s') % (post.thread.forum.name,
                                                 post.thread.title)
    t = loader.get_template('forums/email/new_thread.ltxt')
    c = {'post': post.content, 'author': post.author.username,
         'host': Site.objects.get_current().domain,
         'thread_title': post.thread.title,
         'post_url': post.thread.get_absolute_url()}
    content = t.render(Context(c))
    exclude = (post.thread.creator.email,)

    # Send to forum watchers
    send_notification.delay(forum_ct.id, post.thread.forum.id, subject,
                            content, exclude, 'post')
