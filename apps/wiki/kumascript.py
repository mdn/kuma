import time
from urlparse import urljoin
import json
import base64
import hashlib
from collections import defaultdict

import requests

from django.conf import settings
from django.core.cache import cache
from django.contrib.sites.models import Site

import constance.config

from wiki import KUMASCRIPT_TIMEOUT_ERROR


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
    return (constance.config.KUMASCRIPT_TIMEOUT > 0 and
            html and
            not is_template and
            (force_macros or (not no_macros and not show_raw)))


def post(request, content, locale=settings.LANGUAGE_CODE,
         use_constance_bleach_whitelists=False):
    ks_url = settings.KUMASCRIPT_URL_TEMPLATE.format(path='')
    headers = {
        'X-FireLogger': '1.2',
    }
    env_vars = dict(
        url=request.build_absolute_uri('/'),
        locale=locale
    )
    add_env_headers(headers, env_vars)
    data = content.encode('utf8')
    resp = requests.post(ks_url,
                         timeout=constance.config.KUMASCRIPT_TIMEOUT,
                         data=data,
                         headers=headers)
    if resp:
        resp_body = process_body(resp, use_constance_bleach_whitelists)
        resp_errors = process_errors(resp)
        return resp_body, resp_errors
    else:
        resp_errors = KUMASCRIPT_TIMEOUT_ERROR
        return content, resp_errors


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


def get(document, cache_control, base_url, timeout=None):
    """Perform a kumascript GET request for a document locale and slug."""
    if not cache_control:
        # Default to the configured max-age for cache control.
        max_age = constance.config.KUMASCRIPT_MAX_AGE
        cache_control = 'max-age=%s' % max_age

    if not base_url:
        site = Site.objects.get_current()
        base_url = 'http://%s' % site.domain

    if not timeout:
        timeout = constance.config.KUMASCRIPT_TIMEOUT

    document_locale = document.locale
    document_slug = document.slug
    max_age = constance.config.KUMASCRIPT_MAX_AGE

    resp_body, resp_errors = None, None

    try:
        url_tmpl = settings.KUMASCRIPT_URL_TEMPLATE
        url = unicode(url_tmpl).format(path=u'%s/%s' %
                                       (document_locale, document_slug))

        ck_etag, ck_modified, ck_body, ck_errors = (
                build_cache_keys(document_slug, document_locale))

        headers = {
            'X-FireLogger': '1.2',
            'Cache-Control': cache_control
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
            tags=[x.name for x in document.tags.all()],
            review_tags=[x.name for x in
                         document.current_revision.review_tags.all()],
            modified=time.mktime(document.modified.timetuple()),
            cache_control=cache_control,
        )
        add_env_headers(headers, env_vars)

        # Set up for conditional GET, if we have the details cached.
        c_meta = cache.get_many([ck_etag, ck_modified])
        if ck_etag in c_meta:
            headers['If-None-Match'] = c_meta[ck_etag]
        if ck_modified in c_meta:
            headers['If-Modified-Since'] = c_meta[ck_modified]

        # Finally, fire off the request.
        resp = requests.get(url, headers=headers, timeout=timeout)

        if resp.status_code == 304:
            # Conditional GET was a pass, so use the cached content.
            c_result = cache.get_many([ck_body, ck_errors])
            resp_body = c_result.get(ck_body, '').decode('utf-8')
            resp_errors = c_result.get(ck_errors, None)

        elif resp.status_code == 200:
            resp_body = process_body(resp)
            resp_errors = process_errors(resp)

            # Cache the request for conditional GET, but use the max_age for
            # the cache timeout here too.
            cache.set(ck_etag, resp.headers.get('etag'),
                      timeout=max_age)
            cache.set(ck_modified, resp.headers.get('last-modified'),
                      timeout=max_age)
            cache.set(ck_body, resp_body.encode('utf-8'),
                      timeout=max_age)
            if resp_errors:
                cache.set(ck_errors, resp_errors, timeout=max_age)

        elif resp.status_code is None:
            resp_errors = KUMASCRIPT_TIMEOUT_ERROR

        else:
            resp_errors = [
                {"level": "error",
                  "message": "Unexpected response from Kumascript service: %s"
                             % resp.status_code,
                  "args": ["UnknownError"]}
            ]

    except Exception, e:
        # Last resort: Something went really haywire. Kumascript server died
        # mid-request, or something. Try to report at least some hint.
        resp_errors = [
            {"level": "error",
             "message": "Kumascript service failed unexpectedly: %s" % type(e),
             "args": ["UnknownError"]}
        ]

    return (resp_body, resp_errors)


def add_env_headers(headers, env_vars):
    """Encode env_vars as kumascript headers, as base64 JSON-encoded values."""
    headers.update(dict(
        ('x-kumascript-env-%s' % k, base64.b64encode(json.dumps(v)))
        for k, v in env_vars.items()
    ))
    return headers


def process_body(response, use_constance_bleach_whitelists=False):
    resp_body = response.text

    # We defer bleach sanitation of kumascript content all the way
    # through editing, source display, and raw output. But, we still
    # want sanitation, so it finally gets picked up here.
    from wiki.models import Document
    return Document.objects.clean_content(resp_body,
                                          use_constance_bleach_whitelists)


def process_errors(response):
    """Attempt to decode any FireLogger-style error messages in the response
    from kumascript."""
    resp_errors = []
    try:
        # Extract all the log packets from headers.
        fl_packets = defaultdict(dict)
        for k, v in response.headers.items():
            if not k.lower().startswith('firelogger-'):
                continue
            _, packet_id, seq = k.split('-', 3)
            fl_packets[packet_id][seq] = v

        # The FireLogger spec allows for multiple "packets". But,
        # kumascript only ever sends the one, so flatten all messages.
        fl_msgs = []
        for id, contents in fl_packets.items():
            seqs = sorted(contents.keys(), key=int)
            d_b64 = "\n".join(contents[x] for x in seqs)
            d_json = base64.decodestring(d_b64)
            packet = json.loads(d_json)
            fl_msgs.extend(packet['logs'])

        if len(fl_msgs):
            resp_errors = fl_msgs

    except Exception, e:
        resp_errors = [
            {"level": "error",
              "message": "Problem parsing errors: %s" % e,
              "args": ["ParsingError"]}
        ]
    return resp_errors


def build_cache_keys(document_locale, document_slug):
    """Build the cache keys used for Kumascript"""
    path_hash = hashlib.md5((u'%s/%s' % (document_locale, document_slug))
                            .encode('utf8'))
    cache_key = 'kumascript:%s:%s' % (path_hash.hexdigest(), '%s')
    ck_etag = cache_key % 'etag'
    ck_modified = cache_key % 'modified'
    ck_body = cache_key % 'body'
    ck_errors = cache_key % 'errors'
    return (ck_etag, ck_modified, ck_body, ck_errors)
