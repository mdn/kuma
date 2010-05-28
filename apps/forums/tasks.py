import logging

from django.contrib.contenttypes.models import ContentType
from django.template import Context, loader

from celery.decorators import task
from tower import ugettext as _

from notifications.tasks import send_notification


@task
def build_notification(post):
    ct = ContentType.objects.get_for_model(post.thread)

    subject = _('Reply to: %s') % post.thread.title
    t = loader.get_template('email/new_post.ltxt')
    c = {'post': post.content, 'author': post.author.username,
         'thread_title': post.thread.title,
         'post_url': post.get_absolute_url()}
    content = t.render(Context(c))
    exclude = (post.author.email,)

    send_notification.delay(ct.id, post.thread.id, subject, content, exclude)
