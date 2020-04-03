import logging
import uuid
from urllib.parse import urlencode

import requests
from django.conf import settings
from requests.exceptions import RequestException


log = logging.getLogger("kuma.core.ga_tracking")

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

CATEGORY_SIGNUP_FLOW = "signup-flow"
# Right before redirecting to the auth provider.
ACTION_AUTH_STARTED = "auth-started"
# When redirected back from auth provider and it worked.
ACTION_AUTH_SUCCESSFUL = "auth-successful"
# When we don't need to ask the user to create a profile.
ACTION_RETURNING_USER_SIGNIN = "returning-user-signin"
# Presented with the "Create Profile" form.
ACTION_PROFILE_AUDIT = "profile-audit"
# Have completed the profile creation form.
ACTION_PROFILE_CREATED = "profile-created"
# Have changed a suggested default. E.g. not "peterbe2" but "peterbe_new"
ACTION_PROFILE_EDIT = "profile-edit"
# Have detected an error in the edited profile creation form.
ACTION_PROFILE_EDIT_ERROR = "profile-edit-error"
# Checked or didn't check the "Newsletter" checkbox on sign up.
ACTION_FREE_NEWSLETTER = "free-newsletter"
# When logging in with one provider and benefitting from a verified email
# existing based on a *different* (already created profile) provider.
ACTION_SOCIAL_AUTH_ADD = "social-auth-add"

CATEGORY_MONTHLY_PAYMENTS = "monthly payments"
# When a subscription is successfully set up
ACTION_SUBSCRIPTION_CREATED = "subscription created"
# When it's canceled either by webhook or by UI
ACTION_SUBSCRIPTION_CANCELED = "subscription canceled"
# When a user submits feedback
ACTION_SUBSCRIPTION_FEEDBACK = "feedback"


def track_event(
    event_category,
    event_action,
    event_label,
    client_id=None,
    tracking_id=None,
    tracking_url=None,
    raise_errors=None,
    timeout=None,
):
    """Send an HTTPS POST to Google Analytics for an event.
    The function is, by default, made to be fault tolerant. Any network
    exceptions get swallowed. And connection and read timeouts are held short.

    More information about the Measurement Protocol here:
    https://developers.google.com/analytics/devguides/collection/protocol/v1/devguide
    """
    # The reason we're using `=None` in these and defaulting them to
    # stuff from `settings` down here is for the benefit tests where we
    # might change these values "in runtime". I.e. between tests.
    tracking_id = tracking_id or settings.GOOGLE_ANALYTICS_ACCOUNT
    tracking_url = tracking_url or settings.GOOGLE_ANALYTICS_TRACKING_URL
    timeout = timeout or settings.GOOGLE_ANALYTICS_TRACKING_TIMEOUT
    raise_errors = (
        raise_errors
        if raise_errors is not None
        else settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS
    )

    if not tracking_id:
        return

    client_id = client_id or str(uuid.uuid4())
    params = {
        "v": "1",
        "t": "event",
        "tid": tracking_id,
        "cid": client_id,
        "ec": event_category,
        "ea": event_action,
        "el": event_label,
        "aip": "1",  # anonymize IP
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
            exc_info=True,
        )
