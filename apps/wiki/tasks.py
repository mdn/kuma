import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, mail_admins
from django.db import transaction
from django.template import Context, loader

import celery.conf
from celery.decorators import task
from celery.messaging import establish_connection
from multidb.pinning import pin_this_thread, unpin_this_thread
from tower import ugettext as _

from sumo.urlresolvers import reverse
from sumo.utils import chunked
from wiki.models import Document, SlugCollision, TitleCollision


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
        subject = _('Your revision has been approved: {title}')
    else:
        subject = _('Your revision has been rejected: {title}')
    subject = subject.format(title=document.title)
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

    messages = []
    for pk in data:
        message = None
        try:
            document = Document.objects.get(pk=pk)
            document.html = document.current_revision.content_cleaned
            document.save()
        except Document.DoesNotExist:
            message = 'Missing document: %d' % pk
        except ValidationError as e:
            message = 'ValidationError for %d: %s' % (pk, e.messages[0])
        except SlugCollision:
            message = 'SlugCollision: %d' % pk
        except TitleCollision:
            message = 'TitleCollision: %d' % pk

        if message:
            log.debug(message)
            messages.append(message)

    if messages:
        subject = ('[%s] Exceptions raised in _rebuild_kb_chunk()' %
                   settings.PLATFORM_NAME)
        mail_admins(subject=subject, message='\n'.join(messages))
    transaction.commit_unless_managed()

    unpin_this_thread()  # Not all tasks need to do use the master.
