from __future__ import with_statement

import json
import logging
import os
import textwrap
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sitemaps import GenericSitemap
from django.core.mail import EmailMessage, mail_admins, send_mail
from django.db import connection, transaction
from django.template.loader import render_to_string
from django.utils.encoding import smart_str

from celery import chord, task
from constance import config
from djcelery_transactions import task as transaction_task
from lxml import etree

from kuma.core.cache import memcache
from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.utils import MemcacheLock, chord_flow, chunked
from kuma.search.models import Index

from .events import context_dict
from .exceptions import PageMoveError, StaleDocumentsRenderingInProgress
from .models import Document, DocumentSpamAttempt, Revision, RevisionIP
from .search import WikiDocumentType
from .templatetags.jinja_helpers import absolutify
from .utils import tidy_content


log = logging.getLogger('kuma.wiki.tasks')
render_lock = MemcacheLock('render-stale-documents-lock', expires=60 * 60)


@task(rate_limit='60/m')
@skip_in_maintenance_mode
def render_document(pk, cache_control, base_url, force=False):
    """Simple task wrapper for the render() method of the Document model"""
    document = Document.objects.get(pk=pk)
    if force:
        document.render_started_at = None

    try:
        document.render(cache_control, base_url)
    except Exception as e:
        subject = 'Exception while rendering document %s' % document.pk
        mail_admins(subject=subject, message=e)
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
def update_community_stats():
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT count(creator_id)
            FROM
              (SELECT DISTINCT creator_id
               FROM wiki_revision
               WHERE created >= DATE_SUB(NOW(), INTERVAL 1 YEAR)) AS contributors
            """)
        contributors = cursor.fetchone()

        cursor.execute("""
            SELECT count(locale)
            FROM
              (SELECT DISTINCT wd.locale
               FROM wiki_document wd,
                                  wiki_revision wr
               WHERE wd.id = wr.document_id
                 AND wr.created >= DATE_SUB(NOW(), INTERVAL 1 YEAR)) AS locales
            """)
        locales = cursor.fetchone()
    finally:
        cursor.close()

    community_stats = {}

    try:
        community_stats['contributors'] = contributors[0]
        community_stats['locales'] = locales[0]
    except IndexError:
        community_stats = None

    # storing a None value in cache allows a better check for
    # emptiness in the view
    if 0 in community_stats.values():
        community_stats = None

    memcache.set('community_stats', community_stats, 86400)


@task
@skip_in_maintenance_mode
def delete_old_revision_ips(days=30):
    RevisionIP.objects.delete_old(days=days)


@transaction_task
@skip_in_maintenance_mode
def send_first_edit_email(revision_pk):
    """ Make an 'edited' notification email for first-time editors """
    revision = Revision.objects.get(pk=revision_pk)
    user, doc = revision.creator, revision.document
    subject = (u"[MDN] [%(loc)s] %(user)s made their first edit, to: %(doc)s" %
               {'loc': doc.locale, 'user': user.username, 'doc': doc.title})
    message = render_to_string('wiki/email/edited.ltxt',
                               context_dict(revision))
    doc_url = absolutify(doc.get_absolute_url())
    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL,
                         to=[config.EMAIL_LIST_SPAM_WATCH],
                         headers={'X-Kuma-Document-Url': doc_url,
                                  'X-Kuma-Editor-Username': user.username})
    email.send()


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
    callback save the sitempa index file as well.
    """
    tasks = [build_locale_sitemap.si(locale)
             for locale in settings.MDN_LANGUAGES]
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
