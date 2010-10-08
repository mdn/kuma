from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.template import Context, loader

from celery.decorators import task
from tower import ugettext as _

from notifications.tasks import send_notification


@task
def build_reply_notification(post):
    thread_ct = ContentType.objects.get_for_model(post.thread)
    doc_ct = ContentType.objects.get_for_model(post.thread.document)

    subject = _('Reply to: %s') % post.thread.title
    t = loader.get_template('kbforums/email/new_post.ltxt')
    c = {'post': post.content, 'author': post.creator.username,
         'host': Site.objects.get_current().domain,
         'thread_title': post.thread.title,
         'post_url': post.get_absolute_url()}
    content = t.render(Context(c))
    exclude = (post.creator.email,)

    # Send to thread watchers
    send_notification.delay(thread_ct.id, post.thread.id, subject,
                            content, exclude, 'reply')
    # And document forum watchers
    send_notification.delay(doc_ct.id, post.thread.document.id, subject,
                            content, exclude, 'post')


@task
def build_thread_notification(post):
    doc_ct = ContentType.objects.get_for_model(post.thread.document)

    subject = _('New thread about document %s: %s') % \
        (post.thread.document.title, post.thread.title)
    t = loader.get_template('kbforums/email/new_thread.ltxt')
    c = {'post': post.content, 'author': post.creator.username,
         'host': Site.objects.get_current().domain,
         'thread_title': post.thread.title,
         'post_url': post.thread.get_absolute_url()}
    content = t.render(Context(c))
    exclude = (post.thread.creator.email,)

    # Send to document forum watchers
    send_notification.delay(doc_ct.id, post.thread.document.id, subject,
                            content, exclude, 'post')
