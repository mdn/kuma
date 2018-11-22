import datetime
import json
from time import sleep, time


import redis
import tidylib
from apiclient.discovery import build
from celery.states import READY_STATES
from constance import config
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import resolve, Resolver404
from django.utils import translation
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from six.moves.urllib.parse import urlparse

from kuma.core.urlresolvers import split_path

from .exceptions import NotDocumentView


def locale_and_slug_from_path(path, request=None, path_locale=None):
    """Given a proposed doc path, try to see if there's a legacy MindTouch
    locale or even a modern Kuma domain in the path. If so, signal for a
    redirect to a more canonical path. In any case, produce a locale and
    slug derived from the given path."""
    locale, slug, needs_redirect = '', path, False
    mdn_locales = {lang[0].lower(): lang[0] for lang in settings.LANGUAGES}

    # If there's a slash in the path, then the first segment could be a
    # locale. And, that locale could even be a legacy MindTouch locale.
    if '/' in path:
        maybe_locale, maybe_slug = path.split('/', 1)
        l_locale = maybe_locale.lower()

        if l_locale in settings.MT_TO_KUMA_LOCALE_MAP:
            # The first segment looks like a MindTouch locale, remap it.
            needs_redirect = True
            locale = settings.MT_TO_KUMA_LOCALE_MAP[l_locale]
            slug = maybe_slug

        elif l_locale in mdn_locales:
            # The first segment looks like an MDN locale, redirect.
            needs_redirect = True
            locale = mdn_locales[l_locale]
            slug = maybe_slug

    # No locale yet? Try the locale detected by the request or in path
    if locale == '':
        if request:
            locale = request.LANGUAGE_CODE
        elif path_locale:
            locale = path_locale

    # Still no locale? Probably no request. Go with the site default.
    if locale == '':
        locale = getattr(settings, 'WIKI_DEFAULT_LANGUAGE', 'en-US')

    return (locale, slug, needs_redirect)


def get_doc_components_from_url(url, required_locale=None, check_host=True):
    """Return (locale, path, slug) if URL is a Document, False otherwise.
    If URL doesn't even point to the document view, raise _NotDocumentView.
    """
    # Extract locale and path from URL:
    parsed = urlparse(url)  # Never has errors AFAICT
    if check_host and parsed.netloc:
        # Only allow redirects on our site
        site = urlparse(settings.SITE_URL)
        if parsed.scheme != site.scheme or parsed.netloc != site.netloc:
            return False

    locale, path = split_path(parsed.path)
    if required_locale and locale != required_locale:
        return False

    try:
        with translation.override(locale):
            view, view_args, view_kwargs = resolve(parsed.path)
    except Resolver404:
        return False

    # View imports Model, Model imports utils, utils import Views.
    from kuma.wiki.views.document import document as document_view

    if view != document_view:
        raise NotDocumentView

    path = '/' + path
    return locale, path, view_kwargs['document_path']


def tidy_content(content):
    options = {
        'output-xhtml': 0,
        'force-output': 1,
    }
    try:
        content = tidylib.tidy_document(content, options=options)
    except UnicodeDecodeError:
        # In case something happens in pytidylib we'll try again with
        # a proper encoding
        content = tidylib.tidy_document(content.encode('utf-8'),
                                        options=options)
        tidied, errors = content
        return tidied.decode('utf-8'), errors
    else:
        return content


def analytics_upageviews(revision_ids, start_date, end_date=None):
    """Given a sequence of document revision IDs, returns a dict matching
    those with the number of users Google Analytics thinks has visited
    each revision since start_date.

    """

    scopes = ['https://www.googleapis.com/auth/analytics.readonly']

    try:
        ga_cred_dict = json.loads(config.GOOGLE_ANALYTICS_CREDENTIALS)
    except (ValueError, TypeError):
        raise ImproperlyConfigured(
            "GOOGLE_ANALYTICS_CREDENTIALS Constance setting is badly formed.")
    if not ga_cred_dict:
        raise ImproperlyConfigured(
            "An empty GOOGLE_ANALYTICS_CREDENTIALS Constance setting is not permitted.")

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(ga_cred_dict,
                                                                   scopes=scopes)
    http_auth = credentials.authorize(Http())
    service = build('analyticsreporting', 'v4', http=http_auth)

    if end_date is None:
        end_date = datetime.date.today()

    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()

    request = service.reports().batchGet(
        body={
            'reportRequests': [
                # `dimension12` is the custom variable containing a page's rev #.
                {
                    'dimensions': [{'name': 'ga:dimension12'}],
                    'metrics': [{'expression': 'ga:uniquePageviews'}],
                    'dimensionFilterClauses': [
                        {
                            'filters': [
                                {'dimensionName': 'ga:dimension12',
                                 'operator': 'IN_LIST',
                                 'expressions': map(str, revision_ids)}
                            ]
                        }
                    ],
                    'dateRanges': [
                        {'startDate': start_date, 'endDate': end_date}
                    ],
                    'viewId': '66726481'  # PK of the developer.mozilla.org site on GA.
                }
            ]
        })

    response = request.execute()

    data = {int(r): 0 for r in revision_ids}
    data.update({
        int(row['dimensions'][0]): int(row['metrics'][0]['values'][0])
        for row in response['reports'][0]['data'].get('rows', ())
    })

    return data


def analytics_upageviews_by_revisions(revisions):
    """Given a sequence of Revision objects, returns a dict matching
    their pks with the number of users Google Analytics thinks has visited
    each revision since they were created.
    """
    if not revisions:
        return {}

    revision_ids = [r.id for r in revisions]
    start_date = min(r.created for r in revisions)

    return analytics_upageviews(revision_ids, start_date)


###
# Moved from https://gist.github.com/jwhitlock/43e34e07bef8c3f1863e91f076778ca6
# TODO: Convert into standard celery tasks

_notify_doc_urls = dict()


def notify_rerender_chunk(event, doc_id, task, stream):
    """Print render events."""
    global _notify_doc_urls
    from .models import Document
    if doc_id not in _notify_doc_urls:
        doc = Document.objects.get(id=doc_id)
        _notify_doc_urls[doc_id] = doc.get_full_url()
    doc_url = _notify_doc_urls[doc_id]
    stream.write("Render %s (%s): %d %s" % (event, task.state, doc_id, doc_url))


def rerender_chunk(doc_ids, stuck_time=120, stream=None):
    """
    Queue a set of documents to re-render, and wait until they are done.

    Keyword Arguments:
    doc_ids - A sequence of document IDs to re-render
    stuck_time (120) - The time to wait for the last re-render to complete.
    stream (None) - If set, write document events to this stream

    Return is a tuple of counts (documents rendered, documents unrendered)
    """
    from .tasks import render_document

    tasks = []
    total = len(doc_ids)
    for doc_id in doc_ids:
        task = render_document.delay(doc_id, "no-cache", None, force=True)
        # notifier_func('start', doc_id, task)
        tasks.append((doc_id, task, task.state, False))
    in_progress = len(doc_ids)
    stuck = 0
    while in_progress:
        last_in_progress = in_progress
        in_progress = 0
        next_tasks = []
        for doc_id, task, state, done in tasks:
            if not done:
                state = task.state
                if state in READY_STATES:
                    done = True
                    if stream:
                        notify_rerender_chunk('done', doc_id, task, stream)
                else:
                    in_progress += 1
            next_tasks.append((doc_id, task, state, done))
        tasks = next_tasks
        if last_in_progress == in_progress:
            stuck += 1
        else:
            stuck = 0
        if stuck >= stuck_time:
            for doc_id, task, state, done in tasks:
                if stream and not done:
                    notify_rerender_chunk('stuck', doc_id, task, stream)
            return (total - in_progress, in_progress)
        if in_progress:
            sleep(1)
    return total, 0


def purgable_count():
    """Return the number of tasks in the purgable queue."""
    if settings.BROKER_URL.startswith('redis://'):
        cache = redis.from_url(settings.BROKER_URL)
        return cache.llen('mdn_purgeable')
    else:
        raise ValueError('Not redis broker: %s' % settings.BROKER_URL)


def notify_wait_purgable(event, count, limit, stream):
    """Print purgable count."""
    stream.write("Purgable queue %s: Target depth %d, Current depth %d"
                 % (event, limit, count))


def wait_purgable(limit=1, stream=None):
    """
    Wait for the purgable queue to empty out.

    Keyword arguments:
    limit - Target depth of purgable queue
    stream - If set, print status to this stream
    """
    assert limit >= 0
    try:
        count = purgable_count()
    except ValueError:
        if stream:
            stream.write("Not redis, sleeping for 5 seconds.")
        sleep(5)
        return
    if stream:
        notify_wait_purgable('start', count, limit, stream)
    if count < limit:
        return
    while count > limit:
        sleep(15)
        count = purgable_count()
        if stream:
            notify_wait_purgable('progress', count, limit, stream)


def chunks(items, chunk_size):
    """Yield successive chunk_size-sized chunks from items."""
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def collect_doc_ids(docs, stream=None, doc_filter=None):
    '''Collect the IDs of documents to rerender.'''
    from .models import Document
    raw_doc_ids = list(docs.order_by('id').values_list('id', flat=True))
    if doc_filter:
        if stream:
            stream.write("Processing %d documents for relevant docs..."
                         % len(raw_doc_ids))
        doc_ids = []
        for doc_id in raw_doc_ids:
            doc = Document.objects.get(id=doc_id)
            if doc_filter(doc):
                doc_ids.append(doc_id)
        if stream:
            stream.write("%d of %d documents remain."
                         % (len(doc_ids), len(raw_doc_ids)))
    else:
        doc_ids = raw_doc_ids[:]
    return doc_ids


def errored_doc_ids(doc_ids):
    '''Count documents with KumaScript rendering errors.'''
    from .models import Document
    docs = (Document.objects
            .filter(id__in=doc_ids)
            .exclude(rendered_errors__isnull=True))
    return docs.values_list('id', flat=True)


def rerender_slow(docs, stream=None, limit=100, error_percent=10.0, doc_filter=None):
    '''Re-render a Document queryset a chunk at a time.

    Keyword arguments:
    docs - A queryset of Documents
    stream - A stream for debug messages
    limit - How many to rerender at a time
    error_percent - A float in range (0.0, 100.0], to abort due to KS errors.
    doc_filter - A further filter of doc instances

    Return: A tuple:
    - Total number of docs rendered
    - Total number of docs unrendered (stuck)
    - List of document IDs with kumascript errors
    - Time in seconds it took to re-render slowly
    '''
    start_time = time()
    doc_ids = collect_doc_ids(docs, stream, doc_filter)
    total = len(doc_ids)
    rendered, unrendered, progress = 0, 0, 0
    error_ids = []
    wait_purgable(stream=stream)
    for chunk in chunks(doc_ids, limit):
        progress += len(chunk)
        if stream:
            percent = 100.0 * float(progress) / float(total)
            stream.write("*** Rendering %d of %d docs (%0.1f%%)"
                         % (progress, total, percent))
        chunk_res = rerender_chunk(chunk, stream=stream)
        rendered += chunk_res[0]
        unrendered += chunk_res[1]
        # Wait for purgable queue to clear
        wait_purgable(stream=stream)
        # Count errors
        new_errors = errored_doc_ids(chunk)
        if new_errors and stream:
            stream.write("%d errored documents in last chunk."
                         % len(new_errors))
        error_ids.extend(new_errors)
        error_limit = progress * error_percent / 100.0
        if len(error_ids) >= error_limit:
            if stream:
                stream.write("%d of %d documents have errors, aborting."
                             % (len(error_ids), progress))
            return rendered, unrendered, error_ids, time() - start_time
    return rendered, unrendered, error_ids, time() - start_time
