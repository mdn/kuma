import datetime
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import tidylib

from apiclient.discovery import build
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials

from constance import config


def locale_and_slug_from_path(path, request=None, path_locale=None):
    """Given a proposed doc path, try to see if there's a legacy MindTouch
    locale or even a modern Kuma domain in the path. If so, signal for a
    redirect to a more canonical path. In any case, produce a locale and
    slug derived from the given path."""
    locale, slug, needs_redirect = '', path, False
    mdn_languages_lower = dict((x.lower(), x)
                               for x in settings.MDN_LANGUAGES)

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

        elif l_locale in mdn_languages_lower:
            # The first segment looks like an MDN locale, redirect.
            needs_redirect = True
            locale = mdn_languages_lower[l_locale]
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
