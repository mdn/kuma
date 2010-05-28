import logging

from django.core.mail import send_mass_mail

from celery.decorators import task

from .models import EventWatch

log = logging.getLogger('k.notifications')


@task
def send_notification(content_type, pk, subject, content, exclude=None):
    """Given a content type and ID, subject, and content, get the list of
    watchers and send them email."""

    log.info("Got notification for %s: %s" % (content_type, pk))

    watchers = EventWatch.objects.filter(content_type=content_type,
                                         watch_id=pk)
    if exclude:
        watchers = watchers.exclude(email__in=exclude)

    emails = [(subject, content, 'nobody@example.com', [w.email]) for
              w in watchers]

    send_mass_mail(emails)
