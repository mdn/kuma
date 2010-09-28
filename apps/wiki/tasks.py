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
    log.debug('Sending reviewed email for revision (id=%s)' % revision.id)
    from_address = 'notifications@support.mozilla.com'
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
                                'history_url': url,
                                'host': Site.objects.get_current().domain}))
    send_mail(subject, content, settings.NOTIFICATIONS_FROM_ADDRESS,
              [revision.creator.email])


@task
def send_ready_for_review_notification(revision, document):
    log.debug('Sending ready for review email for revision (id=%s)' %
              revision.id)
    ct = ContentType.objects.get_for_model(document)
    subject = _('%(title)s is ready for review (%(creator)s)' %
                dict(title=document.title, creator=revision.creator))
    url = reverse('wiki.review_revision', locale=document.locale,
                  args=[document.slug, revision.id])
    t = loader.get_template('wiki/email/ready_for_review.ltxt')
    c = {'document_title': document.title,
         'creator': revision.creator,
         'review_url': url,
         'host': Site.objects.get_current().domain}
    content = t.render(Context(c))
    exclude = revision.creator.email,
    send_notification.delay(ct, None, subject, content, exclude,
                            'ready_for_review')
