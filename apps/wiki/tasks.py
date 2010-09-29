import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template import Context, loader

from celery.decorators import task
from tower import ugettext as _

from notifications.tasks import send_notification
from sumo.urlresolvers import reverse


log = logging.getLogger('k.task')


@task
def send_reviewed_notification(revision, document, message):
    """Send notification of review to the revision creator."""
    log.debug('Sending reviewed email for revision (id=%s)' % revision.id)
    if revision.is_approved:
        subject = _('Your revision has been approved: %s')
    else:
        subject = _('Your revision has been rejected: %s')
    subject = subject % document.title
    t = loader.get_template('wiki/email/reviewed.ltxt')
    url = reverse('wiki.document_revisions', locale=document.locale,
                  args=[document.slug])
    content = t.render(Context({'document_title': document.title,
                                'approved': revision.is_approved,
                                'reviewer': revision.reviewer,
                                'message': message,
                                'url': url,
                                'host': Site.objects.get_current().domain}))
    send_mail(subject, content, settings.NOTIFICATIONS_FROM_ADDRESS,
              [revision.creator.email])


@task
def send_ready_for_review_notification(revision, document):
    """Send notification that a new revision is ready for review."""
    log.debug('Sending ready for review email for revision (id=%s)' %
              revision.id)
    subject = _('%(title)s is ready for review (%(creator)s)')
    url = reverse('wiki.review_revision', locale=document.locale,
                  args=[document.slug, revision.id])
    _send_notification(revision, document, subject,
                       'wiki/email/ready_for_review.ltxt', url,
                       'ready_for_review')


@task
def send_edited_notification(revision, document):
    """Send notification of new revision to watchers of the document."""
    log.debug('Sending edited notification email for document (id=%s)' %
              document.id)
    subject = _('%(title)s was edited by %(creator)s')
    url = reverse('wiki.document_revisions', locale=document.locale,
                  args=[document.slug])
    _send_notification(revision, document, subject, 'wiki/email/edited.ltxt',
                       url, 'edited')


def _send_notification(revision, document, subject, template, url, event_type):
    subject = subject % dict(title=document.title, creator=revision.creator)
    t = loader.get_template(template)
    c = {'document_title': document.title,
         'creator': revision.creator,
         'url': url,
         'host': Site.objects.get_current().domain}
    content = t.render(Context(c))
    exclude = revision.creator.email,
    ct = ContentType.objects.get_for_model(document)
    id = None if event_type == 'ready_for_review' else document.id
    send_notification.delay(ct, id, subject, content, exclude,
                            event_type)
