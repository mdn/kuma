from __future__ import with_statement

import json
import logging
import os
import textwrap
from datetime import datetime, timedelta

from celery import chord, task
from celery.result import AsyncResult
from celery.states import READY_STATES, SUCCESS
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sitemaps import GenericSitemap
from django.core.mail import mail_admins, send_mail
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from djcelery_transactions import task as transaction_task
from lxml import etree

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.utils import CacheLock, chord_flow, chunked
from kuma.search.models import Index

from .events import first_edit_email
from .exceptions import PageMoveError, StaleDocumentsRenderingInProgress
from .models import (Document, DocumentDeletionLog,
                     DocumentRenderingInProgress, DocumentSpamAttempt,
                     Revision, RevisionIP)
from .rerender import (DocumentInProcess, load_batch, load_job,
                       NoRegenerationBatch, RegenerationBatch, store_batch,
                       store_job)
from .search import WikiDocumentType
from .templatetags.jinja_helpers import absolutify
from .utils import purgable_count, tidy_content


log = logging.getLogger('kuma.wiki.tasks')
render_lock = CacheLock('render-stale-documents-lock', expires=60 * 60)


@task(rate_limit='60/m')
@skip_in_maintenance_mode
def render_document(pk, cache_control, base_url, force=False):
    """Simple task wrapper for the render() method of the Document model"""
    document = Document.objects.get(pk=pk)
    if force:
        document.render_started_at = None

    try:
        document.render(cache_control, base_url)
    except DocumentRenderingInProgress:
        pass
    except Exception as e:
        subject = 'Exception while rendering document %s' % document.pk
        mail_admins(subject=subject, message=str(e))
    return document.rendered_errors


@task
@skip_in_maintenance_mode
def email_render_document_progress(percent_complete, total):
    """
    Task to send email for render_document progress notification.
    """
    subject = ('The command `render_document` is %s%% complete' %
               percent_complete)
    message = (
        'The command `render_document` is %s%% complete out of a total of '
        '%s documents to render.' % (percent_complete, total))
    mail_admins(subject=subject, message=message)


@task
@skip_in_maintenance_mode
def render_document_chunk(pks, cache_control='no-cache', base_url=None,
                          force=False):
    """
    Simple task to render a chunk of documents instead of one per each
    """
    logger = render_document_chunk.get_logger()
    logger.info(u'Starting to render document chunk: %s' %
                ','.join([str(pk) for pk in pks]))
    base_url = base_url or settings.SITE_URL
    for pk in pks:
        # calling the task without delay here since we want to localize
        # the processing of the chunk in one process
        result = render_document(pk, cache_control, base_url, force=force)
        if result:
            logger.error(u'Error while rendering document %s with error: %s' %
                         (pk, result))
    logger.info(u'Finished rendering of document chunk')


@task(throws=(StaleDocumentsRenderingInProgress,))
@skip_in_maintenance_mode
def acquire_render_lock():
    """
    A task to acquire the render document lock
    """
    if render_lock.locked():
        # fail loudly if this is running already
        # may indicate a problem with the schedule of this task
        raise StaleDocumentsRenderingInProgress
    render_lock.acquire()


@task
@skip_in_maintenance_mode
def release_render_lock():
    """
    A task to release the render document lock
    """
    render_lock.release()


@task
@skip_in_maintenance_mode
def render_stale_documents(log=None):
    """Simple task wrapper for rendering stale documents"""
    stale_docs = Document.objects.get_by_stale_rendering().distinct()
    stale_docs_count = stale_docs.count()
    if stale_docs_count == 0:
        # not stale documents to render
        return

    if log is None:
        # fetch a logger in case none is given
        log = render_stale_documents.get_logger()

    log.info('Found %s stale documents' % stale_docs_count)
    stale_pks = stale_docs.values_list('pk', flat=True)

    pre_task = acquire_render_lock.si()
    render_tasks = [render_document_chunk.si(pks)
                    for pks in chunked(stale_pks, 5)]
    post_task = release_render_lock.si()

    chord_flow(pre_task, render_tasks, post_task).apply_async()


@task
@skip_in_maintenance_mode
def build_json_data_for_document(pk, stale):
    """Force-refresh cached JSON data after rendering."""
    document = Document.objects.get(pk=pk)
    document.get_json_data(stale=stale)

    # If we're a translation, rebuild our source doc's JSON so its
    # translation list includes our last edit date.
    if document.parent is not None:
        parent_json = json.dumps(document.parent.build_json_data())
        Document.objects.filter(pk=document.parent.pk).update(json=parent_json)


@task
@skip_in_maintenance_mode
def move_page(locale, slug, new_slug, user_id):
    transaction.set_autocommit(False)
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        transaction.rollback()
        logging.error('Page move failed: no user with id %s' % user_id)
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
        send_mail('Page move failed',
                  textwrap.dedent(message),
                  settings.DEFAULT_FROM_EMAIL,
                  [user.email])
        transaction.set_autocommit(True)
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
        send_mail('Page move failed',
                  textwrap.dedent(message),
                  settings.DEFAULT_FROM_EMAIL,
                  [user.email])
        transaction.set_autocommit(True)
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
        send_mail('Page move failed',
                  textwrap.dedent(message),
                  settings.DEFAULT_FROM_EMAIL,
                  [user.email])
        transaction.set_autocommit(True)
        return

    transaction.commit()
    transaction.set_autocommit(True)

    # Now that we know the move succeeded, re-render the whole tree.
    for moved_doc in [doc] + doc.get_descendants():
        moved_doc.schedule_rendering('max-age=0')

    subject = 'Page move completed: ' + slug + ' (' + locale + ')'

    full_url = settings.SITE_URL + '/' + locale + '/docs/' + new_slug

    # Get the parent document, if parent doc is None, it means its the parent document
    parent_doc = doc.parent or doc

    other_locale_urls = [settings.SITE_URL + translation.get_absolute_url()
                         for translation in parent_doc.translations.exclude(locale=doc.locale)
                                                                   .order_by('locale')]

    # If the document is a translation we should include the parent document url to the list
    if doc.parent:
        other_locale_urls = [settings.SITE_URL + doc.parent.get_absolute_url()] + other_locale_urls

    message = textwrap.dedent("""
        Page move completed.

        The move requested for the document with slug %(slug)s in locale
        %(locale)s, and all its children, has been completed.

        The following localized articles may need to be moved also:
        %(locale_urls)s

        You can now view this document at its new location: %(full_url)s.
    """) % {'slug': slug, 'locale': locale, 'full_url': full_url,
            'locale_urls': '\n'.join(other_locale_urls)}

    send_mail(subject,
              message,
              settings.DEFAULT_FROM_EMAIL,
              [user.email])


@task
@skip_in_maintenance_mode
def delete_old_revision_ips(days=30):
    RevisionIP.objects.delete_old(days=days)


@transaction_task
@skip_in_maintenance_mode
def send_first_edit_email(revision_pk):
    """ Make an 'edited' notification email for first-time editors """
    revision = Revision.objects.get(pk=revision_pk)
    first_edit_email(revision).send()


class WikiSitemap(GenericSitemap):
    protocol = 'https'
    priority = 0.5


SITEMAP_START = u'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
SITEMAP_ELEMENT = u'<sitemap><loc>%s</loc><lastmod>%s</lastmod></sitemap>'
SITEMAP_END = u'</sitemapindex>'


@task
def build_locale_sitemap(locale):
    """
    For the given locale build the appropriate sitemap file and
    returns the locale, the file names written and timestamp of the
    build.
    """
    now = datetime.utcnow()
    timestamp = '%s+00:00' % now.replace(microsecond=0).isoformat()

    directory = os.path.join(settings.MEDIA_ROOT, 'sitemaps', locale)
    if not os.path.isdir(directory):
        os.makedirs(directory)

    queryset = Document.objects.filter_for_list(locale=locale)
    if queryset.exists():
        names = []
        info = {
            'queryset': queryset,
            'date_field': 'modified',
        }
        sitemap = WikiSitemap(info)
        for page in range(1, sitemap.paginator.num_pages + 1):
            urls = sitemap.get_urls(page=page)
            if page == 1:
                name = 'sitemap.xml'
            else:
                name = 'sitemap_%s.xml' % page
            names.append(name)

            rendered = smart_str(render_to_string('wiki/sitemap.xml',
                                                  {'urls': urls}))
            path = os.path.join(directory, name)
            with open(path, 'w') as sitemap_file:
                sitemap_file.write(rendered)

        return locale, names, timestamp


@task
def build_index_sitemap(results):
    """
    A chord callback task that writes a sitemap index file for the
    given results of :func:`~kuma.wiki.tasks.build_locale_sitemap` task.
    """
    sitemap_parts = [SITEMAP_START]

    for result in results:
        # result can be empty if no documents were found
        if result is not None:
            locale, names, timestamp = result
            for name in names:
                sitemap_url = absolutify('/sitemaps/%s/%s' % (locale, name))
                sitemap_parts.append(SITEMAP_ELEMENT % (sitemap_url, timestamp))

    sitemap_parts.append(SITEMAP_END)

    index_path = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')
    sitemap_tree = etree.fromstringlist(sitemap_parts)
    with open(index_path, 'w') as index_file:
        sitemap_tree.getroottree().write(index_file,
                                         encoding='utf-8',
                                         pretty_print=True)


@task
def build_sitemaps():
    """
    Build and save sitemap files for every MDN language and as a
    callback save the sitemap index file as well.
    """
    tasks = [build_locale_sitemap.si(lang[0]) for lang in settings.LANGUAGES]
    post_task = build_index_sitemap.s()
    # we retry the chord unlock 300 times, so 5 mins with an interval of 1s
    chord(header=tasks, body=post_task).apply_async(max_retries=300, interval=1)


@task
@skip_in_maintenance_mode
def index_documents(ids, index_pk, reraise=False):
    """
    Index a list of documents into the provided index.

    :arg ids: Iterable of `Document` pks to index.
    :arg index_pk: The `Index` pk of the index to index into.
    :arg reraise: False if you want errors to be swallowed and True
        if you want errors to be thrown.

    .. Note::

       This indexes all the documents in the chunk in one single bulk
       indexing call. Keep that in mind when you break your indexing
       task into chunks.

    """
    from kuma.wiki.models import Document

    cls = WikiDocumentType
    es = cls.get_connection('indexing')
    index = Index.objects.get(pk=index_pk)

    objects = Document.objects.filter(id__in=ids)
    documents = []
    for obj in objects:
        try:
            documents.append(cls.from_django(obj))
        except Exception:
            log.exception('Unable to extract/index document (id: %d)', obj.id)
            if reraise:
                raise

    if documents:
        cls.bulk_index(documents, id_field='id', es=es,
                       index=index.prefixed_name)


@task
@skip_in_maintenance_mode
def unindex_documents(ids, index_pk):
    """
    Delete a list of documents from the provided index.

    :arg ids: Iterable of `Document` pks to remove.
    :arg index_pk: The `Index` pk of the index to remove items from.
    """
    cls = WikiDocumentType
    es = cls.get_connection('indexing')
    index = Index.objects.get(pk=index_pk)

    cls.bulk_delete(ids, es=es, index=index.prefixed_name)


@task(rate_limit='120/m')
@skip_in_maintenance_mode
def tidy_revision_content(pk, refresh=True):
    """
    Run tidy over the given revision's content and save it to the
    tidy_content field if the content is not equal to the current value.

    :arg pk: Primary key of `Revision` whose content needs tidying.
    """
    try:
        revision = Revision.objects.get(pk=pk)
    except Revision.DoesNotExist as exc:
        # Retry in 2 minutes
        log.error('Tidy was unable to get revision id: %d. Retrying.', pk)
        tidy_revision_content.retry(countdown=60 * 2, max_retries=5, exc=exc)
    else:
        if revision.tidied_content and not refresh:
            return
        tidied_content, errors = tidy_content(revision.content)
        if tidied_content != revision.tidied_content:
            Revision.objects.filter(pk=pk).update(
                tidied_content=tidied_content
            )
        # return the errors so we can look them up in the Celery task result
        return errors


@task
@skip_in_maintenance_mode
def delete_old_documentspamattempt_data(days=30):
    """Delete old DocumentSpamAttempt.data, which contains PII.

    Also set review to REVIEW_UNAVAILABLE.
    """
    older = datetime.now() - timedelta(days=30)
    dsas = DocumentSpamAttempt.objects.filter(
        created__lt=older).exclude(data__isnull=True)
    dsas_reviewed = dsas.exclude(review=DocumentSpamAttempt.NEEDS_REVIEW)
    dsas_unreviewed = dsas.filter(review=DocumentSpamAttempt.NEEDS_REVIEW)
    dsas_reviewed.update(data=None)
    dsas_unreviewed.update(
        data=None, review=DocumentSpamAttempt.REVIEW_UNAVAILABLE)


@task
@skip_in_maintenance_mode
def delete_logs_for_purged_documents():
    """Delete DocumentDeletionLogs for purged documents."""
    for ddl in DocumentDeletionLog.objects.all():
        doc = Document.admin_objects.filter(locale=ddl.locale, slug=ddl.slug)
        if not doc.exists():
            ddl.delete()


@task
def rerender_step1_rough_count(job_id):
    """Get a rough count and estimate of the documents to rerender."""
    from .models import Document

    # Load job
    job = load_job(job_id)
    assert job['state'] == 'waiting'

    # Cancel the job?
    now = datetime.now()
    job['timestamps']['heartbeat'] = now
    if settings.MAINTENANCE_MODE or job['canceled']:
        store_job(job)
        rerender_step6_finalize.delay(job_id)
        return

    # Update to current state
    job['state'] = 'rough_count'
    job['timestamps']['rough_count'] = now
    store_job(job)

    # Get rough filter
    docs = Document.objects.all()
    filters = job['filter_params']
    if filters['locales']:
        docs = docs.filter(locale__in=filters['locales'])
    if filters['macros']:
        macros = filters['macros']
        macro_q = Q(html__icontains=macros[0].lower())
        for macro in macros[1:]:
            macro_q |= Q(html__icontains=macro.lower())
        docs = docs.filter(macro_q)
    rough_count = docs.count()
    raw_doc_ids = list(docs.order_by('id').values_list('id', flat=True))

    # Initialize the batch
    batch = RegenerationBatch(data={'to_filter_ids': raw_doc_ids,
                                    'chunk': []})
    assert batch.is_valid()
    batch_data = batch.validated_data
    store_batch(batch_data)

    # Update job with rough count and estimate
    job['counts']['rough'] = rough_count
    now = datetime.now()
    job['timestamps']['heartbeat'] = now
    job['estimate'] = now + timedelta(seconds=rough_count)
    job['batch_id'] = batch_data['batch_id']
    store_job(job)

    # Schedule next step
    rerender_step2_detailed_count.delay(job_id)


@task
def rerender_step2_detailed_count(job_id):
    from .models import Document

    # Load job, batch
    job = load_job(job_id)
    assert job['state'] == 'rough_count'
    assert job['batch_id']
    batch = load_batch(job['batch_id'])

    # Cancel the job?
    now = datetime.now()
    job['timestamps']['heartbeat'] = now
    if settings.MAINTENANCE_MODE or job['canceled']:
        store_job(job)
        rerender_step6_finalize.delay(job_id)
        return

    # Update to current state
    job['state'] = 'detailed_count'
    job['timestamps']['detailed_count'] = now
    store_job(job)

    # If macros are specified, we need a detailed count
    to_do_ids = []
    filter_macros = [m.lower() for m in job['filter_params']['macros']]
    for doc_id in batch['to_filter_ids']:
        if filter_macros:
            # Check that the document uses the macro before rerendering
            try:
                doc = Document.objects.get(id=doc_id)
            except Document.DoesNotExist:
                continue
            doc_macros = set([m.lower() for m in doc.extract.macro_names()])
            match = any((macro in doc_macros for macro in filter_macros))
        else:
            # Rough filter is enough to include document
            match = True

        if match:
            to_do_ids.append(doc_id)

    # Update batch with filtered IDs
    batch['to_filter_ids'] = []
    batch['to_do_ids'] = to_do_ids
    store_batch(batch)

    # Update job with detailed count and estimate
    detailed_count = len(to_do_ids)
    job['counts']['detailed'] = detailed_count
    now = datetime.now()
    job['timestamps']['heartbeat'] = now
    job['estimate'] = now + timedelta(seconds=detailed_count)
    store_job(job)

    # Schedule next step
    rerender_step3_start_batch.delay(job_id)


@task
def rerender_step3_start_batch(job_id):
    """Start re-rendering a batch of documents."""
    # Load job, batch
    job = load_job(job_id)
    assert job['state'] in ('detailed_count', 'cool_down')
    assert job['batch_id']
    batch = load_batch(job['batch_id'])
    assert batch['chunk'] == []

    # Cancel the job?
    now = datetime.now()
    job['timestamps']['heartbeat'] = now
    if settings.MAINTENANCE_MODE or job['canceled']:
        store_job(job)
        rerender_step6_finalize.delay(job_id)
        return

    # Update to current state
    job['state'] = 'rendering'
    if not job['timestamps']['render']:
        job['timestamps']['render'] = now
    job['estimate'] = now + timedelta(seconds=len(batch['to_do_ids']))
    store_job(job)

    # If the error ratio is too high, then abort
    if job['counts']['errored']:
        errored = job['counts']['errored']
        rendered = job['counts']['rendered']
        err_percent = float(errored) / float(errored + rendered)
        if err_percent >= job['error_percent']:
            job['state'] = 'errored'
            store_job(job)
            rerender_step6_finalize.delay(job_id)
            return

    # If we're done rendering, then finalize
    if len(batch['to_do_ids']) == 0:
        rerender_step6_finalize.delay(job_id)
        return

    # Pick the next chunk of IDs
    batch_size = job['batch_size']
    chunk_ids = batch['to_do_ids'][:batch_size]
    batch['to_do_ids'] = batch['to_do_ids'][batch_size:]

    # Start rerendering
    rerender_start = datetime.now()
    for doc_id in chunk_ids:
        render_task = render_document.delay(doc_id, "no-cache", None,
                                            force=True)
        process_data = {
            'doc_id': doc_id,
            'task_id': render_task.id,
            'task_state': render_task.state,
            'change_time': rerender_start
        }
        in_process = DocumentInProcess(data=process_data)
        assert in_process.is_valid()
        batch['chunk'].append(in_process.validated_data)

    # Update batch and job
    store_batch(batch)
    job['timestamps']['heartbeat'] = datetime.now()
    job['counts']['in_progress'] = len(batch['chunk'])
    store_job(job)

    # Check re-render status in a few seconds
    countdown = job['batch_interval']
    rerender_step4_check_batch.apply_async(args=(job_id,), countdown=countdown)


@task
def rerender_step4_check_batch(job_id):
    """Check the status of a batch of rerendering documents."""
    # Load job, batch
    job = load_job(job_id)
    assert job['state'] == 'rendering'
    assert job['batch_id']
    batch = load_batch(job['batch_id'])
    assert batch['chunk']

    # Set the heartbeat
    now = datetime.now()
    job['timestamps']['heartbeat'] = now

    # Cancel the job?
    if settings.MAINTENANCE_MODE or job['canceled']:
        store_job(job)
        rerender_step6_finalize.delay(job_id)
        return

    # Check rerendering status
    check_start = datetime.now()
    last_change = job['timestamps']['render']  # An old time
    docs_success = []
    docs_errored = []
    docs_in_progress = []
    for in_progress in batch['chunk']:
        doc_id = in_progress['doc_id']
        old_state = in_progress['state']
        if old_state in READY_STATES:
            # Already complete
            new_state = old_state
        else:
            # Ask Celery for new state
            render_task = AsyncResult(in_progress['task_id'])
            new_state = render_task.state
            if new_state != old_state:
                in_progress['change_time'] = check_start
                last_change = check_start

        if new_state == SUCCESS:
            docs_success.append(doc_id)
        elif new_state in READY_STATES:
            # READY_STATES is SUCCESS plus error states
            docs_errored.append(doc_id)
        else:
            docs_in_progress.append(doc_id)

    # Are the re-render jobs stuck?
    stuck_time = timedelta(job['stuck_time'])
    is_stuck = (now - last_change) > stuck_time
    chunk_done = is_stuck or len(docs_in_progress) == 0

    if chunk_done:
        # End of re-render, finalize chunk
        from .models import Document

        # Split successful docs by kumascript rendering errors
        errored_ids = set(Document.objects
                          .filter(id__in=docs_success)
                          .exclude(rendered_errors__isnull=True)
                          .values_list('id', flat=True))
        ks_errors = [doc for doc in docs_success if doc in errored_ids]
        ks_success = [doc for doc in docs_success if doc not in errored_ids]

        # Update categorized document IDs in batch
        batch['errored_ids'].extend(sorted(docs_errored + ks_errors))
        batch['stuck_ids'].extend(docs_in_progress)
        batch['done_ids'].extend(ks_success)
        batch['chunk'] = []

        # Update counts for the document
        job['counts']['errored'] = len(batch['errored_ids'])
        job['counts']['rendered'] = len(batch['done_ids'])
        job['counts']['abandoned'] = len(batch['stuck_ids'])
        job['counts']['in_progress'] = 0

        # Add some recent docs
        doc_urls = []
        for doc_id in ks_errors:
            doc = Document.objects.get(id=doc_id)
            doc_urls.append(doc.get_absolute_url())
        for doc_id in ks_success[:5]:
            doc = Document.objects.get(id=doc_id)
            doc_urls.append(doc.get_absolute_url())
        job['recent_docs'] = doc_urls

        # Next, wait for the purgable task queue to empty
        job['tasks_max_seen'] = None
        job['tasks_current'] = None
        next_task = rerender_step5_empty_task_queue
    else:
        # Continue waiting for rerender
        job['counts']['errored'] = (len(batch['errored_ids']) +
                                    len(docs_errored))
        job['counts']['rendered'] = len(batch['done_ids']) + len(docs_success)
        job['counts']['abandoned'] = len(batch['stuck_ids'])
        job['counts']['in_progress'] = len(docs_in_progress)

        # Next, check the task status again
        next_task = rerender_step4_check_batch

    # Update batch and job
    store_batch(batch)
    job['timestamps']['heartbeat'] = datetime.now()
    store_job(job)

    # Check re-render status again in a few seconds
    countdown = job['batch_interval']
    next_task.apply_async(args=(job_id,), countdown=countdown)


@task
def rerender_step5_empty_task_queue(job_id):
    """
    Wait for the purgable task queue to calm down.

    Re-rendering a document starts several follow-on tasks, to extract
    in-content data and update metadata. Wait for the depth of the
    purgable queue to die down before starting a new chunk of work.
    """

    # Load job, batch
    job = load_job(job_id)
    assert job['state'] in ('rendering', 'cool_down')
    job['state'] = 'cool_down'

    # Cancel the job?
    now = datetime.now()
    job['timestamps']['heartbeat'] = now
    if settings.MAINTENANCE_MODE or job['canceled']:
        store_job(job)
        rerender_step6_finalize.delay(job_id)
        return

    # Update purgable task count
    current = purgable_count()
    job['tasks_max_seen'] = max(job['tasks_max_seen'], current)
    job['tasks_current'] = current
    store_job(job)

    if current <= job['tasks_goal']:
        # Start next batch
        rerender_step3_start_batch.delay(job_id)
    else:
        countdown = job['batch_interval']
        rerender_step5_empty_task_queue.apply_async(args=(job_id,),
                                                    countdown=countdown)


@task
def rerender_step6_finalize(job_id):
    """Finalize a re-render job."""
    # Load job
    job = load_job(job_id)
    try:
        batch = load_batch(job['batch_id'])
    except NoRegenerationBatch:
        batch = None

    job['timestamps']['done'] = datetime.now()

    # Was the job canceled?
    if settings.MAINTENANCE_MODE or job['canceled']:
        job['state'] = 'canceled'

    # Set the job to done, if still in an active state
    if job['state'] not in ('canceled', 'errored', 'orphaned'):
        job['state'] = 'done'

    # Finalize counts
    if batch:
        job['counts']['errored'] = len(batch['errored_ids'])
        job['counts']['rendered'] = len(batch['done_ids'])
        job['counts']['abandoned'] = (len(batch['to_filter_ids']) +
                                      len(batch['to_do_ids']) +
                                      len(batch['chunk']))
        job['counts']['in_progress'] = 0

    # TODO: Email report

    store_job(job)
