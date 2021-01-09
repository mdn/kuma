import base64
import json
import time
import unicodedata
from collections import defaultdict
from functools import partial
from urllib.parse import urljoin

import requests
from constance import config
from django.conf import settings
from django.contrib.sites.models import Site
from requests.exceptions import ConnectionError, ReadTimeout

from .constants import KUMASCRIPT_BASE_URL
from .content import clean_content


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
    show_raw = params.get("raw", False) is not False
    no_macros = params.get("nomacros", False) is not False
    force_macros = params.get("macros", False) is not False
    if doc:
        html = doc.html
    return (
        config.KUMASCRIPT_TIMEOUT > 0
        and html
        and (force_macros or (not no_macros and not show_raw))
    )


def _post(content, env_vars, cache_control=None, timeout=None):
    url = settings.KUMASCRIPT_URL_TEMPLATE.format(path="")
    headers = {
        "X-FireLogger": "1.2",
    }

    # If the user does a hard reload we see Cache-Control:no-cache in
    # the request header. And we pass that header on to Kumascript so
    # that it does not use its cache when re-rendering the page.
    if cache_control == "no-cache":
        headers["Cache-Control"] = cache_control

    # Load just-in-time, since constance requires DB and cache
    # TODO: Move to a standard Django setting w/ env override
    if timeout is None:
        timeout = config.KUMASCRIPT_TIMEOUT

    add_env_headers(headers, env_vars)

    try:
        response = requests.post(
            url, data=content.encode(), headers=headers, timeout=timeout
        )
    except (ConnectionError, ReadTimeout) as err:
        error = {
            "level": "error",
            "message": str(err),
            "args": [err.__class__.__name__],
        }
        return content, [error]

    body = process_body(response)
    errors = process_errors(response)
    return body, errors


def post(request, content, locale=settings.LANGUAGE_CODE):
    return _post(content, {"url": request.build_absolute_uri("/"), "locale": locale})


# TODO(djf): This get() function is actually implemented on top of
# _post() and it performs an HTTP POST request. It should probably
# be renamed to render_document(), and the post() method above should
# be renamed to render_string(), maybe. For now, though, there are so
# many tests that mock kumascript.get() that I've left the name unchanged.
def get(document, base_url, cache_control=None, timeout=None, selective_mode=None):
    """Request a rendered version of document.html from KumaScript."""

    if not base_url:
        site = Site.objects.get_current()
        base_url = "http://%s" % site.domain

    # Assemble some KumaScript env vars
    path = document.get_absolute_url()

    env_vars = dict(
        path=path,
        url=urljoin(base_url, path),
        id=document.pk,
        revision_id=document.current_revision.pk,
        locale=document.locale,
        title=document.title,
        slug=document.slug,
        tags=list(document.tags.names()),
        review_tags=list(document.current_revision.review_tags.names()),
        modified=time.mktime(document.modified.timetuple()),
        selective_mode=selective_mode,
    )

    return _post(document.html, env_vars, cache_control, timeout)


def add_env_headers(headers, env_vars):
    """Encode env_vars as kumascript headers, as base64 JSON-encoded values."""
    headers.update(
        dict(
            (
                "x-kumascript-env-%s" % k,
                base64.b64encode(json.dumps(v).encode()).decode(),
            )
            for k, v in env_vars.items()
        )
    )
    return headers


def process_body(response):
    # We defer bleach sanitation of kumascript content all the way
    # through editing, source display, and raw output. But, we still
    # want sanitation, so it finally gets picked up here.
    return clean_content(response.text)


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
            if not key.lower().startswith("firelogger-"):
                continue
            prefix, id_, seq = key.split("-", 3)
            packets[id_][seq] = value

        # The FireLogger spec allows for multiple "packets". But,
        # kumascript only ever sends the one, so flatten all messages.
        msgs = []
        for contents in packets.values():
            keys = sorted(contents.keys(), key=int)
            encoded = "\n".join(contents[key] for key in keys)
            decoded_json = base64.decodebytes(encoded.encode())
            packet = json.loads(decoded_json)
            msgs.extend(packet["logs"])

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


def macro_sources(force_lowercase_keys=False):
    """
    Get active macros and their source paths.

    Return is a dict with the case-sensitive macro name as key, and the subpath
    on GitHub as the value.  The full URL of the GitHub source is:
    https://github.com/mdn/kumascript/tree/master/macros/{subpath}
    """
    ks_macro_url = urljoin(KUMASCRIPT_BASE_URL, "macros/")
    response = requests.get(ks_macro_url)
    if response.status_code == 200:
        macros_raw = response.json()["macros"]
        # Ensure Normal Form C used on GitHub
        normalize_key = normalize = partial(unicodedata.normalize, "NFC")
        if force_lowercase_keys:
            normalize_key = lambda x: normalize(x).lower()  # noqa: E731
        return {
            normalize_key(md["name"]): normalize(md["filename"]) for md in macros_raw
        }
    else:
        return {}


def request_revision_hash():
    ks_revision_url = urljoin(KUMASCRIPT_BASE_URL, "revision/")
    return requests.get(ks_revision_url, timeout=config.KUMASCRIPT_TIMEOUT)
