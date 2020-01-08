import logging
import uuid
from urllib.parse import urlencode

import requests
from django.conf import settings
from requests.exceptions import RequestException


log = logging.getLogger('kuma.core.ga_tracking')

# The `track_event()` function can take any string but to minimize risk of
# typos, it's highly recommended to use a constant instead.
# Instead of doing:
#
#   # somefile.py
#   from ga_tracking import track_event
#   track_event('signup-flow', 'foo', 'bar')
#
#   # otherfile.py
#   from ga_tracking import track_event
#   track_event('signup-fluw', 'foo', 'bar')
#
# Do this instead:
#
#   # somefile.py
#   from ga_tracking import track_event, CATEGORY_SIGNUP_FLOW
#   track_event(CATEGORY_SIGNUP_FLOW, 'foo', 'bar')
#
#   # otherfile.py
#   from ga_tracking import track_event, CATEGORY_SIGNUP_FLOW
#   track_event(CATEGORY_SIGNUP_FLOW, 'foo', 'bar')
#
# Here are some of those useful constants...

CATEGORY_SIGNUP_FLOW = 'signup-flow'
ACTION_SIGN_UP = 'sign-up'
ACTION_SIGN_IN = 'sign-in'


def track_event(
    event_category,
    event_action,
    event_label,
    client_id=None,
    tracking_id=settings.GOOGLE_ANALYTICS_ACCOUNT,
    tracking_url=settings.GOOGLE_ANALYTICS_TRACKING_URL,
    raise_errors=settings.DEBUG,
    timeout=settings.GOOGLE_ANALYTICS_EVENTS_TRACKING_TIMEOUT,
):
    """Send an HTTPS POST to Google Analytics for an event.
    The function is, by default, made to be fault tolerant. Any network
    exceptions get swallowed. And connection and read timeouts are held short.

    More information about the Measurement Protocol here:
    https://developers.google.com/analytics/devguides/collection/protocol/v1/devguide
    """
    tracking_id = settings.GOOGLE_ANALYTICS_ACCOUNT
    if not tracking_id:
        return

    client_id = client_id or str(uuid.uuid4())
    params = {
        'v': '1',
        't': 'event',
        'tid': tracking_id,
        'cid': client_id,
        'ec': event_category,
        'ea': event_action,
        'el': event_label,
        'aip': '1'  # anonymize IP
    }
    url = f"{tracking_url}?{urlencode(params)}"
    try:
        response = requests.post(url, timeout=timeout)
        if raise_errors:
            response.raise_for_status()
    except RequestException:
        if raise_errors:
            raise
        log.error(
            "Failed sending GA tracking event "
            f"{event_category!r}, {event_action!r}, {event_label!r}",
            exc_info=True)
