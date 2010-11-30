import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.template import Context, loader

import celery.conf
from celery.decorators import task
from celery.messaging import establish_connection
from multidb.pinning import pin_this_thread, unpin_this_thread
from tower import ugettext as _

from notifications.tasks import send_notification
from sumo.urlresolvers import reverse
from sumo.utils import chunked
from wiki.models import Document


log = logging.getLogger('k.task')


@task
def send_reviewed_notification(revision, document, message):
    """Send notification of review to the revision creator."""
    if revision.reviewer == revision.creator:
        log.debug('Revision (id=%s) reviewed by creator, skipping email' % \
                  revision.id)
        return

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
                       'ready_for_review', document.locale)


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


def _send_notification(revision, document, subject, template, url, event_type,
                       locale=''):
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
                            event_type, locale)


def schedule_rebuild_kb():
    """Try to schedule a KB rebuild, if we're allowed to."""
    if not settings.WIKI_REBUILD_ON_DEMAND or celery.conf.ALWAYS_EAGER:
        return

    if cache.get(settings.WIKI_REBUILD_TOKEN):
        log.debug('Rebuild task already scheduled.')
        return

    cache.set(settings.WIKI_REBUILD_TOKEN, True)

    rebuild_kb.delay()


@task(rate_limit='3/h')
def rebuild_kb():
    """Re-render all documents in the KB in chunks."""
    cache.delete(settings.WIKI_REBUILD_TOKEN)

    d = (Document.objects.using('default')
         .filter(current_revision__isnull=False).values_list('id', flat=True))

    with establish_connection() as conn:
        for chunk in chunked(d, 100):
            _rebuild_kb_chunk.apply_async(args=[chunk],
                                          connection=conn)


@task(rate_limit='10/m')
def _rebuild_kb_chunk(data, **kwargs):
    """Re-render a chunk of documents."""
    log.info('Rebuilding %s documents.' % len(data))

    pin_this_thread()  # Stick to master.

    for pk in data:
        try:
            document = Document.objects.get(pk=pk)
            document.html = document.current_revision.content_parsed
            document.save()
        except Document.DoesNotExist:
            log.debug('Missing document: %d' % pk)
    transaction.commit_unless_managed()

    unpin_this_thread()  # Not all tasks need to do use the master.
