import logging

from django.core.mail import send_mass_mail
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from celery.decorators import task

from notifications.models import EventWatch, Watch

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

    sent = send_mass_mail(emails, fail_silently=True)

    if sent != len(emails):
        log.warning('Tried to send %s emails, but only sent %s' %
                    (len(emails), sent))


@task(rate_limit='4/m')
def delete_watches(cls, pk):
    ct = ContentType.objects.get_for_model(cls)
    log.info('Deleting watches for %s %s' % (ct, pk))
    e = EventWatch.uncached.using('default').filter(
        content_type=ct, watch_id=pk)
    e.delete()


@task(rate_limit='20/m')
def update_email_in_notifications(old, new):
    """Change the email in notifications from old to new."""
    log.info(u'Changing email %s to %s' % (old, new))
    EventWatch.objects.filter(email=old).update(email=new)


@task(rate_limit='1/m')
def claim_watches(user):
    """Look for anonymous watches with this user's email and attach them to the
    user."""
    Watch.objects.filter(email=user.email).update(email=None, user=user)
