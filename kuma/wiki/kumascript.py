import base64
import hashlib
import json
import time
import unicodedata
from collections import defaultdict
from functools import partial

import requests
from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.utils.six.moves.urllib.parse import urljoin
from elasticsearch import TransportError

from .constants import KUMASCRIPT_BASE_URL, KUMASCRIPT_TIMEOUT_ERROR
from .content import clean_content
from .inline_examples import INLINE_EXAMPLES
from .search import WikiDocumentType


def should_use_rendered(doc, params, html=None):
    """
      * The service isn't disabled with a timeout of 0
      * The document isn't empty
      * The request has *not* asked for raw source
        (eg. ?raw)
      * The request has *not* asked for no macro evaluation
        (eg. ?nomacros)
      * The request *has* asked for macro evaluation
        (eg. ?raw&macros)
    """
    show_raw = params.get('raw', False) is not False
    no_macros = params.get('nomacros', False) is not False
    force_macros = params.get('macros', False) is not False
    if doc:
        html = doc.html
    return (config.KUMASCRIPT_TIMEOUT > 0 and
            html and
            (force_macros or (not no_macros and not show_raw)))


def post(request, content, locale=settings.LANGUAGE_CODE):
    url = settings.KUMASCRIPT_URL_TEMPLATE.format(path='')
    headers = {
        'X-FireLogger': '1.2',
    }
    env_vars = {
        'url': request.build_absolute_uri('/'),
        'locale': locale,
    }
    add_env_headers(headers, env_vars)
    response = requests.post(url,
                             timeout=config.KUMASCRIPT_TIMEOUT,
                             data=content.encode('utf8'),
                             headers=headers)
    if response:
        body = process_body(response)
        errors = process_errors(response)
        return body, errors
    else:
        errors = KUMASCRIPT_TIMEOUT_ERROR
        return content, errors


def _get_attachment_metadata_dict(attachment):
    current_revision = attachment.current_revision
    try:
        filesize = current_revision.file.size
    except OSError:
        filesize = 0
    return {
        'title': current_revision.title,
        'description': current_revision.description,
        'filename': current_revision.filename,
        'size': filesize,
        'author': current_revision.creator.username,
        'mime': current_revision.mime_type,
        'url': attachment.get_file_url(),
    }


def get(document, cache_control, base_url, timeout=None):
    """Perform a kumascript GET request for a document locale and slug."""
    if not cache_control:
        # Default to the configured max-age for cache control.
        max_age = config.KUMASCRIPT_MAX_AGE
        cache_control = 'max-age=%s' % max_age

    if not base_url:
        site = Site.objects.get_current()
        base_url = 'http://%s' % site.domain

    if not timeout:
        timeout = config.KUMASCRIPT_TIMEOUT

    document_locale = document.locale
    document_slug = document.slug
    max_age = config.KUMASCRIPT_MAX_AGE

    # 1063580 - Kumascript converts template name calls to lower case and bases
    # caching keys off of that.
    document_slug_for_kumascript = document_slug
    body, errors = None, None

    try:
        url_tmpl = settings.KUMASCRIPT_URL_TEMPLATE
        url = unicode(url_tmpl).format(path=u'%s/%s' %
                                       (document_locale,
                                        document_slug_for_kumascript))

        cache_keys = build_cache_keys(document_slug, document_locale)
        etag_key, modified_key, body_key, errors_key = cache_keys

        headers = {
            'X-FireLogger': '1.2',
            'Cache-Control': cache_control,
        }

        # Create the file interface
        files = []
        for attachment in document.files.select_related('current_revision'):
            files.append(_get_attachment_metadata_dict(attachment))

        # Assemble some KumaScript env vars
        # TODO: See dekiscript vars for future inspiration
        # http://developer.mindtouch.com/en/docs/DekiScript/Reference/
        #   Wiki_Functions_and_Variables
        path = document.get_absolute_url()
        # TODO: Someday merge with _get_document_for_json in views.py
        # where most of this is duplicated code.
        env_vars = dict(
            path=path,
            url=urljoin(base_url, path),
            id=document.pk,
            revision_id=document.current_revision.pk,
            locale=document.locale,
            title=document.title,
            files=files,
            attachments=files,  # Just for sake of verbiage?
            slug=document.slug,
            tags=list(document.tags.names()),
            review_tags=list(document.current_revision.review_tags.names()),
            modified=time.mktime(document.modified.timetuple()),
            cache_control=cache_control,
        )
        add_env_headers(headers, env_vars)

        # Set up for conditional GET, if we have the details cached.
        cached_meta = cache.get_many([etag_key, modified_key])
        if etag_key in cached_meta:
            headers['If-None-Match'] = cached_meta[etag_key]
        if modified_key in cached_meta:
            headers['If-Modified-Since'] = cached_meta[modified_key]

        # Finally, fire off the request.
        response = requests.get(url, headers=headers, timeout=timeout)

        if response.status_code == 304:
            # Conditional GET was a pass, so use the cached content.
            result = cache.get_many([body_key, errors_key])
            body = result.get(body_key, '').decode('utf-8')
            errors = result.get(errors_key, None)

        elif response.status_code == 200:
            body = process_body(response)
            errors = process_errors(response)

            # Cache the request for conditional GET, but use the max_age for
            # the cache timeout here too.
            headers = response.headers
            cache.set(etag_key, headers.get('etag'), timeout=max_age)
            cache.set(modified_key, headers.get('last-modified'), timeout=max_age)
            cache.set(body_key, body.encode('utf-8'), timeout=max_age)
            if errors:
                cache.set(errors_key, errors, timeout=max_age)

        elif response.status_code is None:
            errors = KUMASCRIPT_TIMEOUT_ERROR

        else:
            errors = [
                {
                    "level": "error",
                    "message": "Unexpected response from Kumascript service: %s" %
                               response.status_code,
                    "args": ["UnknownError"],
                },
            ]

    except Exception as exc:
        # Last resort: Something went really haywire. Kumascript server died
        # mid-request, or something. Try to report at least some hint.
        errors = [
            {
                "level": "error",
                "message": "Kumascript service failed unexpectedly: %s" % exc,
                "args": ["UnknownError"],
            },
        ]
    return (body, errors)


def add_env_headers(headers, env_vars):
    """Encode env_vars as kumascript headers, as base64 JSON-encoded values."""
    headers.update(dict(
        ('x-kumascript-env-%s' % k, base64.b64encode(json.dumps(v)))
        for k, v in env_vars.items()
    ))
    return headers


def process_body(response):
    # We defer bleach sanitation of kumascript content all the way
    # through editing, source display, and raw output. But, we still
    # want sanitation, so it finally gets picked up here.
    clean_response = clean_content(response.text)
    # After sanitization perform a final pass to substitute any inlined
    # interactive example macros
    return process_inlined_examples(clean_response)


def process_inlined_examples(body):
    """
    Manually expand @InlineMacro@ declarations
    """
    return body \
        .replace("@InlineArrayForEach@", INLINE_EXAMPLES["FOR_EACH"]) \
        .replace("@InlineArrayMap@", INLINE_EXAMPLES["MAP"]) \
        .replace("@InlineArrayFilter@", INLINE_EXAMPLES["FILTER"]) \
        .replace("@InlineArrayFind@", INLINE_EXAMPLES["FIND"]) \
        .replace("@InlineArrayReduce@", INLINE_EXAMPLES["REDUCE"]) \
        .replace("@InlineArraySplice@", INLINE_EXAMPLES["SPLICE"])


def process_errors(response):
    """
    Attempt to decode any FireLogger-style error messages in the response
    from kumascript.
    """
    errors = []
    try:
        # Extract all the log packets from headers.
        packets = defaultdict(dict)
        for key, value in response.headers.items():
            if not key.lower().startswith('firelogger-'):
                continue
            prefix, id_, seq = key.split('-', 3)
            packets[id_][seq] = value

        # The FireLogger spec allows for multiple "packets". But,
        # kumascript only ever sends the one, so flatten all messages.
        msgs = []
        for contents in packets.values():
            keys = sorted(contents.keys(), key=int)
            encoded = '\n'.join(contents[key] for key in keys)
            decoded_json = base64.decodestring(encoded)
            packet = json.loads(decoded_json)
            msgs.extend(packet['logs'])

        if len(msgs):
            errors = msgs

    except Exception as exc:
        errors = [
            {
                "level": "error",
                "message": "Problem parsing errors: %s" % exc,
                "args": ["ParsingError"],
            },
        ]
    return errors


def build_cache_keys(document_locale, document_slug):
    """Build the cache keys used for Kumascript"""
    path_hash = hashlib.md5((u'%s/%s' % (document_locale, document_slug))
                            .encode('utf8'))
    base_key = 'kumascript:%s:%%s' % path_hash.hexdigest()
    etag_key = base_key % 'etag'
    modified_key = base_key % 'modified'
    body_key = base_key % 'body'
    errors_key = base_key % 'errors'
    return (etag_key, modified_key, body_key, errors_key)


def macro_sources(force_lowercase_keys=False):
    """
    Get active macros and their source paths.

    Return is a dict with the case-sensitive macro name as key, and the subpath
    on GitHub as the value.  The full URL of the GitHub source is:
    https://github.com/mdn/kumascript/tree/master/macros/{subpath}
    """
    ks_macro_url = urljoin(KUMASCRIPT_BASE_URL, 'macros/')
    response = requests.get(ks_macro_url)
    if response.status_code == 200:
        macros_raw = response.json()['macros']
        # Ensure Normal Form C used on GitHub
        normalize_key = normalize = partial(unicodedata.normalize, 'NFC')
        if force_lowercase_keys:
            normalize_key = lambda x: normalize(x).lower()
        return {
            normalize_key(md['name']): normalize(md['filename'])
            for md in macros_raw
        }
    else:
        return {}


def macro_page_count(locale='*'):
    """
    Get the macros known to ElasticSearch with their page counts

    Return is a dictionary of lowercase macro names to their page counts.
    This includes things that look like macros, such as Django templates from
    the Django learning area, and anything wrapped in {{ }}.

    Keyword Arguments:
    locale - Filter by this locale (default no locale filter)
    """
    search = WikiDocumentType.search().extra(size=0)  # Return no documents
    search.aggs.bucket('usage', 'terms', field='kumascript_macros',
                       size=2000)  # Set to larger than number of macros
    if locale != '*':
        search = search.filter("term", locale=locale)
    result = search.execute()  # Could raise TransportError
    return {item['key']: item['doc_count'] for item
            in result.aggregations.usage.buckets}


def macro_usage():
    """
    Get active macros, their source paths, and usage on site.

    Return is a dict with the case-sensitive macro name as key, and a dict as
    value with keys:
    * github_subpath - the subpath on GitHub
    * count - the number of pages the macro is used on
    * en_count - the number of English pages the macro is used on

    If there is no ElasticSearch server or it is misconfigured, then the
    counts will both be 0.
    """

    # Get active macros from KumaScript, returning early if none.
    macro_paths = macro_sources()
    if not macro_paths:
        return {}

    # Convert macro sources to fuller dict
    lowercase_names = {}
    macros = {}
    for name, github_subpath in macro_paths.items():
        macros[name] = {
            'github_subpath': github_subpath,
            'count': 0,
            'en_count': 0
        }
        lowercase_names[name.lower()] = name

    def annotate_counts(counts, count_type):
        """Record document counts from an ElasticSearch annotated result."""
        for lowercase_name, doc_count in counts.items():
            try:
                name = lowercase_names[lowercase_name]
            except KeyError:
                pass
            else:
                macros[name][count_type] = doc_count

    # Record page usage for active macros for all locales
    try:
        all_counts = macro_page_count()
    except TransportError:
        # For the first call, gracefully handle missing ES server, etc.
        return macros
    else:
        annotate_counts(all_counts, 'count')

    # Record page usage for active macros for English
    # For second call, ES Server issue _is_ exceptional, raise error
    annotate_counts(macro_page_count('en-US'), 'en_count')

    return macros


def request_revision_hash():
    ks_revision_url = urljoin(KUMASCRIPT_BASE_URL, 'revision/')
    return requests.get(ks_revision_url, timeout=config.KUMASCRIPT_TIMEOUT)
