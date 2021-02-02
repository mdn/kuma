from unittest.mock import MagicMock

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from ..middleware import (
    ForceAnonymousSessionMiddleware,
    SetRemoteAddrFromForwardedFor,
    WaffleWithCookieDomainMiddleware,
)


@pytest.mark.parametrize(
    "forwarded_for,remote_addr",
    (("1.1.1.1", "1.1.1.1"), ("2.2.2.2", "2.2.2.2"), ("3.3.3.3, 4.4.4.4", "3.3.3.3")),
)
def test_set_remote_addr_from_forwarded_for(rf, forwarded_for, remote_addr):
    """SetRemoteAddrFromForwardedFor parses the X-Forwarded-For Header."""
    rf = RequestFactory()
    middleware = SetRemoteAddrFromForwardedFor(lambda req: None)
    request = rf.get("/", HTTP_X_FORWARDED_FOR=forwarded_for)
    middleware(request)
    assert request.META["REMOTE_ADDR"] == remote_addr


def test_force_anonymous_session_middleware(rf, settings):
    request = rf.get("/foo")
    request.COOKIES[settings.SESSION_COOKIE_NAME] = "totallyfake"

    mock_response = MagicMock()
    middleware = ForceAnonymousSessionMiddleware(lambda req: mock_response)
    response = middleware(request)

    assert request.session
    assert request.session.session_key is None
    assert not response.method_calls


def test_waffle_cookie_domain_middleware(rf, settings):
    settings.WAFFLE_COOKIE = "dwf_%s"
    settings.WAFFLE_COOKIE_DOMAIN = "mdn.dev"
    resp = HttpResponse()
    resp.set_cookie("some_key", "some_value", domain=None)
    resp.set_cookie("another_key", "another_value", domain="another.domain")
    middleware = WaffleWithCookieDomainMiddleware(lambda req: resp)
    request = rf.get("/foo")
    request.waffles = {
        "contrib_beta": (True, False),
        "developer_needs": (True, False),
    }
    response = middleware(request)
    assert response.cookies["some_key"]["domain"] == ""
    assert response.cookies["another_key"]["domain"] == "another.domain"
    assert response.cookies["dwf_contrib_beta"]["domain"] == "mdn.dev"
    assert response.cookies["dwf_developer_needs"]["domain"] == "mdn.dev"
