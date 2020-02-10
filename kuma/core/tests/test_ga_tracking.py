import pytest
from requests.exceptions import ConnectionError, HTTPError

from ..ga_tracking import track_event


def test_happy_path(settings, mock_requests):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    mock_requests.register_uri("POST", settings.GOOGLE_ANALYTICS_TRACKING_URL)
    track_event("category", "action", "label")


def test_nothing_happens_if_no_ga_account(settings, mock_requests):
    # Sanity check fixtures
    assert not settings.GOOGLE_ANALYTICS_ACCOUNT
    # This would raise NoMockAddress if it did something.
    track_event("category", "action", "label")


def test_errors_swallowed(settings, mock_requests):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = False
    mock_requests.register_uri(
        "POST", settings.GOOGLE_ANALYTICS_TRACKING_URL, exc=ConnectionError
    )
    track_event("category", "action", "label")
    # unless they're not...
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = True
    with pytest.raises(ConnectionError):
        track_event("category", "action", "label")


def test_bad_responses_swallowed(settings, mock_requests):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = False
    mock_requests.register_uri(
        "POST", settings.GOOGLE_ANALYTICS_TRACKING_URL, status_code=500
    )
    track_event("category", "action", "label")
    # unless they're not...
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = True
    with pytest.raises(HTTPError):
        track_event("category", "action", "label", raise_errors=True)
