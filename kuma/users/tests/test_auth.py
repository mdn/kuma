from django.test import RequestFactory

from kuma.users.auth import logout_url


# TODO: Check which new tests are needed.
def test_logout_url(settings):
    request = RequestFactory().get("/some/path")
    request.session = {}
    url = logout_url(request)
    assert url == "/"

    request = RequestFactory().get("/some/path?next=/docs")
    request.session = {}
    url = logout_url(request)
    assert url == "/docs"

    settings.LOGOUT_REDIRECT_URL = "/loggedout"
    request = RequestFactory().get("/some/path")
    request.session = {}
    url = logout_url(request)
    assert url == "/loggedout"

    request.session["oidc_login_next"] = "/original"
    url = logout_url(request)
    assert url == "/original"
