import datetime
import json
from urllib.parse import urlparse

import tidylib
from constance import config
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import resolve, Resolver404
from django.utils import translation
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials

from kuma.core.urlresolvers import split_path

from .exceptions import NotDocumentView


def locale_and_slug_from_path(path, request=None, path_locale=None):
    """Given a proposed doc path, try to see if there's a legacy MindTouch
    locale or even a modern Kuma domain in the path. If so, signal for a
    redirect to a more canonical path. In any case, produce a locale and
    slug derived from the given path."""
    locale, slug, needs_redirect = "", path, False
    mdn_locales = {lang[0].lower(): lang[0] for lang in settings.LANGUAGES}

    # If there's a slash in the path, then the first segment could be a
    # locale. And, that locale could even be a legacy MindTouch locale.
    if "/" in path:
        maybe_locale, maybe_slug = path.split("/", 1)
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
    if locale == "":
        if request:
            locale = request.LANGUAGE_CODE
        elif path_locale:
            locale = path_locale

    # Still no locale? Probably no request. Go with the site default.
    if locale == "":
        locale = getattr(settings, "WIKI_DEFAULT_LANGUAGE", "en-US")

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
    from kuma.wiki.views.document import (
        document as document_view,
        react_document as react_document_view,
    )

    if view not in (document_view, react_document_view):
        raise NotDocumentView

    path = "/" + path
    return locale, path, view_kwargs["document_path"]


def tidy_content(content):
    options = {
        "output-xhtml": 0,
        "force-output": 1,
    }
    try:
        content = tidylib.tidy_document(content, options=options)
    except UnicodeDecodeError:
        # In case something happens in pytidylib we'll try again with
        # a proper encoding
        content = tidylib.tidy_document(content.encode(), options=options)
        tidied, errors = content
        return tidied.decode(), errors
    else:
        return content


def analytics_upageviews(revision_ids, start_date, end_date=None):
    """Given a sequence of document revision IDs, returns a dict matching
    those with the number of users Google Analytics thinks has visited
    each revision since start_date.

    """

    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]

    try:
        ga_cred_dict = json.loads(config.GOOGLE_ANALYTICS_CREDENTIALS)
    except (ValueError, TypeError):
        raise ImproperlyConfigured(
            "GOOGLE_ANALYTICS_CREDENTIALS Constance setting is badly formed."
        )
    if not ga_cred_dict:
        raise ImproperlyConfigured(
            "An empty GOOGLE_ANALYTICS_CREDENTIALS Constance setting is not permitted."
        )

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        ga_cred_dict, scopes=scopes
    )
    http_auth = credentials.authorize(Http())
    service = build("analyticsreporting", "v4", http=http_auth)

    if end_date is None:
        end_date = datetime.date.today()

    if hasattr(start_date, "date"):
        start_date = start_date.date()
    if hasattr(end_date, "date"):
        end_date = end_date.date()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()

    request = service.reports().batchGet(
        body={
            "reportRequests": [
                # `dimension12` is the custom variable containing a page's rev #.
                {
                    "dimensions": [{"name": "ga:dimension12"}],
                    "metrics": [{"expression": "ga:uniquePageviews"}],
                    "dimensionFilterClauses": [
                        {
                            "filters": [
                                {
                                    "dimensionName": "ga:dimension12",
                                    "operator": "IN_LIST",
                                    "expressions": [str(x) for x in revision_ids],
                                }
                            ]
                        }
                    ],
                    "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                    "viewId": "66726481",  # PK of the developer.mozilla.org site on GA.
                }
            ]
        }
    )

    response = request.execute()

    data = {int(r): 0 for r in revision_ids}
    data.update(
        {
            int(row["dimensions"][0]): int(row["metrics"][0]["values"][0])
            for row in response["reports"][0]["data"].get("rows", ())
        }
    )

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
