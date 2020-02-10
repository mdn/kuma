from unittest.mock import MagicMock

import pytest
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse
from django.test import RequestFactory

from ..middleware import (
    ForceAnonymousSessionMiddleware,
    RestrictedEndpointsMiddleware,
    SetRemoteAddrFromForwardedFor,
    WaffleWithCookieDomainMiddleware,
)


@pytest.mark.parametrize("path", ("/missing_url", "/missing_url/"))
def test_slash_middleware_keep_404(client, db, path):
    """The SlashMiddleware retains 404s."""
    response = client.get(path)
    assert response.status_code == 404


def test_slash_middleware_removes_slash(client, db):
    """The SlashMiddleware fixes a URL that shouldn't have a trailing slash."""
    response = client.get("/contribute.json/")
    assert response.status_code == 301
    assert response["Location"].endswith("/contribute.json")


@pytest.mark.parametrize("path", ("/admin", "/en-US"))
def test_slash_middleware_adds_slash(path, client, db):
    """The SlashMiddleware fixes a URL that should have a trailing slash."""
    response = client.get(path)
    assert response.status_code == 301
    assert response["Location"].endswith(path + "/")


def test_slash_middleware_retains_querystring(client, db):
    """The SlashMiddleware handles encoded querystrings."""
    response = client.get("/contribute.json/?xxx=%C3%83")
    assert response.status_code == 301
    assert response["Location"].endswith("/contribute.json?xxx=%C3%83")


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


@pytest.mark.parametrize(
    "host,key,expected",
    (
        ("wiki", "WIKI_HOST", None),
        ("demos", "ATTACHMENT_HOST", "kuma.urls_untrusted"),
        ("demos-origin", "ATTACHMENT_ORIGIN", "kuma.urls_untrusted"),
    ),
    ids=("wiki", "attachment", "attachment-origin"),
)
def test_restricted_endpoints_middleware(rf, settings, host, key, expected):
    setattr(settings, key, host)
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    settings.ALLOWED_HOSTS.append(host)
    middleware = RestrictedEndpointsMiddleware(lambda req: None)
    request = rf.get("/foo", HTTP_HOST=host)
    middleware(request)
    if expected:
        assert request.urlconf == expected
    else:
        assert not hasattr(request, "urlconf")


def test_restricted_endpoints_middleware_when_disabled(settings):
    settings.ENABLE_RESTRICTIONS_BY_HOST = False
    with pytest.raises(MiddlewareNotUsed):
        RestrictedEndpointsMiddleware(lambda req: None)


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
