import logging

from django.core.mail import send_mass_mail
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from celery.decorators import task

from .models import EventWatch

log = logging.getLogger('k.notifications')


@task
def send_notification(content_type, pk, subject, content, exclude=None,
                      event_type='reply', locale=''):
    """Given a content type and ID, event type, subject, and content, get
    the list of watchers and send them email."""

    log.info('Got %s notification for %s: %s' % (event_type, content_type,
                                                 pk))

    watchers = EventWatch.uncached.using('default').filter(
        content_type=content_type, watch_id=pk, event_type=event_type,
        locale=locale)
    if exclude:
        watchers = watchers.exclude(email__in=exclude)

    emails = [(subject, content, settings.NOTIFICATIONS_FROM_ADDRESS,
               [w.email]) for w in watchers]

    send_mass_mail(emails)


@task(rate_limit='4/m')
def delete_watches(cls, pk):
    ct = ContentType.objects.get_for_model(cls)
    log.info('Deleting watches for %s %s' % (ct, pk))
    e = EventWatch.uncached.using('default').filter(
        content_type=ct, watch_id=pk)
    e.delete()
