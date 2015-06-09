import base64
from collections import defaultdict
import json
import hashlib
import time
from urlparse import urljoin

from django.conf import settings
from django.contrib.sites.models import Site

from constance import config
import requests

from kuma.core.cache import memcache

from .constants import KUMASCRIPT_TIMEOUT_ERROR, TEMPLATE_TITLE_PREFIX


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
    is_template = False
    if doc:
        is_template = doc.is_template
        html = doc.html
    return (config.KUMASCRIPT_TIMEOUT > 0 and
            html and
            not is_template and
            (force_macros or (not no_macros and not show_raw)))


def post(request, content, locale=settings.LANGUAGE_CODE,
         use_constance_bleach_whitelists=False):
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
        body = process_body(response, use_constance_bleach_whitelists)
        errors = process_errors(response)
        return body, errors
    else:
        errors = KUMASCRIPT_TIMEOUT_ERROR
        return content, errors


def _get_attachment_metadata_dict(attachment):
    filesize = 0
    try:
        filesize = attachment.current_revision.file.size
    except OSError:
        pass
    return {
        'title': attachment.title,
        'description': attachment.current_revision.description,
        'filename': attachment.current_revision.filename(),
        'size': filesize,
        'author': attachment.current_revision.creator.username,
        'mime': attachment.current_revision.mime_type,
        'url': attachment.get_file_url(),
    }


def _format_slug_for_request(slug):
    """Formats a document slug which will play nice with kumascript caching"""
    # http://bugzil.la/1063580
    index = slug.find(TEMPLATE_TITLE_PREFIX)
    if index != -1:
        slug = '%s%s' % (TEMPLATE_TITLE_PREFIX, slug[(index + len(TEMPLATE_TITLE_PREFIX)):].lower())
    return slug


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
    if document.is_template:
        document_slug_for_kumascript = _format_slug_for_request(document_slug)

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
        for attachment in document.attachments.all():
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
            tags=list(document.tags.values_list('name', flat=True)),
            review_tags=list(document.current_revision
                                     .review_tags
                                     .values_list('name', flat=True)),
            modified=time.mktime(document.modified.timetuple()),
            cache_control=cache_control,
        )
        add_env_headers(headers, env_vars)

        # Set up for conditional GET, if we have the details cached.
        cached_meta = memcache.get_many([etag_key, modified_key])
        if etag_key in cached_meta:
            headers['If-None-Match'] = cached_meta[etag_key]
        if modified_key in cached_meta:
            headers['If-Modified-Since'] = cached_meta[modified_key]

        # Finally, fire off the request.
        response = requests.get(url, headers=headers, timeout=timeout)

        if response.status_code == 304:
            # Conditional GET was a pass, so use the cached content.
            result = memcache.get_many([body_key, errors_key])
            body = result.get(body_key, '').decode('utf-8')
            errors = result.get(errors_key, None)

        elif response.status_code == 200:
            body = process_body(response)
            errors = process_errors(response)

            # Cache the request for conditional GET, but use the max_age for
            # the cache timeout here too.
            headers = response.headers
            memcache.set(etag_key, headers.get('etag'), timeout=max_age)
            memcache.set(modified_key, headers.get('last-modified'), timeout=max_age)
            memcache.set(body_key, body.encode('utf-8'), timeout=max_age)
            if errors:
                memcache.set(errors_key, errors, timeout=max_age)

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

    except Exception, exc:
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


def process_body(response, use_constance_bleach_whitelists=False):
    # We defer bleach sanitation of kumascript content all the way
    # through editing, source display, and raw output. But, we still
    # want sanitation, so it finally gets picked up here.
    from kuma.wiki.models import Document
    return Document.objects.clean_content(response.text,
                                          use_constance_bleach_whitelists)


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

    except Exception, exc:
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
