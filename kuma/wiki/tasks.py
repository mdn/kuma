import logging

from celery.task import task, group

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.dispatch import receiver

import waffle

from devmo.utils import MemcacheLock
from .exceptions import StaleDocumentsRenderingInProgress, PageMoveError
from .models import Document
from .signals import render_done


log = logging.getLogger('k.task')


@task(rate_limit='60/m')
def render_document(pk, cache_control, base_url):
    """Simple task wrapper for the render() method of the Document model"""
    document = Document.objects.get(pk=pk)
    document.render(cache_control, base_url)
    return document.rendered_errors


@task
def render_stale_documents(immediate=False, log=None):
    """Simple task wrapper for rendering stale documents"""
    lock = MemcacheLock('render-stale-documents-lock')
    if lock.acquired and not immediate:
        # fail loudly if this is running already
        # may indicate a problem with the schedule of this task
        raise StaleDocumentsRenderingInProgress

    stale_docs = Document.objects.get_by_stale_rendering()
    stale_docs_count = stale_docs.count()
    if stale_docs_count == 0:
        # not stale documents to render
        return

    if log is None:
        # fetch a logger in case none is given
        log = render_stale_documents.get_logger()

    log.info("Found %s stale documents" % stale_docs_count)
    response = None
    if lock.acquire():
        try:
            subtasks = []
            for doc in stale_docs:
                if immediate:
                    doc.render('no-cache', settings.SITE_URL)
                    log.info("Rendered stale %s" % doc)
                else:
                    subtask = render_document.subtask((doc.pk, 'no-cache',
                                                       settings.SITE_URL))
                    subtasks.append(subtask)
                    log.info("Deferred rendering for stale %s" % doc)
            if subtasks:
                task_group = group(tasks=subtasks)
                if waffle.switch_is_active('render_stale_documents_async'):
                    # kick off the task group asynchronously
                    task_group.apply_async()
                else:
                    # kick off the task group synchronously
                    result = task_group.apply()
                    response = result.join()
        finally:
            lock.release()
    return response


@task
def build_json_data_for_document_task(pk, stale):
    """Force-refresh cached JSON data after rendering."""
    document = Document.objects.get(pk=pk)
    document.get_json_data(stale=stale)


@receiver(render_done)
def build_json_data_handler(sender, instance, **kwargs):
    try:
        build_json_data_for_document_task.delay(instance.pk, stale=False)
    except:
        logging.error('JSON metadata build task failed',
                      exc_info=True)


@task
def move_page(locale, slug, new_slug, email):
    with transaction.commit_manually():
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            transaction.rollback()
            logging.error('Page move failed: no user with email address %s' %
                          email)
            return
        try:
            doc = Document.objects.get(locale=locale, slug=slug)
        except Document.DoesNotExist:
            transaction.rollback()
            message = """
    Page move failed.

    Move was requested for document with slug %(slug)s in locale
    %(locale)s, but no such document exists.
            """ % {'slug': slug, 'locale': locale}
            logging.error(message)
            send_mail('Page move failed', message, settings.DEFAULT_FROM_EMAIL,
                      [user.email])
            return
        try:
            doc._move_tree(new_slug, user=user)
        except PageMoveError as e:
            transaction.rollback()
            message = """
    Page move failed.

    Move was requested for document with slug %(slug)s in locale
    %(locale)s, but could not be completed.

    Diagnostic info:

    %(message)s
            """ % {'slug': slug, 'locale': locale, 'message': e.message}
            logging.error(message)
            send_mail('Page move failed', message, settings.DEFAULT_FROM_EMAIL,
                      [user.email])
            return
        except Exception as e:
            transaction.rollback()
            message = """
    Page move failed.

    Move was requested for document with slug %(slug)s in locale %(locale)s,
    but could not be completed.

    %(info)s
            """ % {'slug': slug, 'locale': locale, 'info': e}
            logging.error(message)
            send_mail('Page move failed', message, settings.DEFAULT_FROM_EMAIL,
                      [user.email])
            return

        transaction.commit()

    # Now that we know the move succeeded, re-render the whole tree.
    for moved_doc in [doc] + doc.get_descendants():
        moved_doc.schedule_rendering('max-age=0')

    subject = 'Page move completed: ' + slug + ' (' + locale + ')'
    full_url = settings.SITE_URL + '/' + locale + '/docs/' + new_slug
    message = """
Page move completed.

The move requested for the document with slug %(slug)s in locale
%(locale)s, and all its children, has been completed.

You can now view this document at its new location: %(full_url)s.
    """ % {'slug': slug, 'locale': locale, 'full_url': full_url}
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
              [user.email])
