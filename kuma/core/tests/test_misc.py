from django.test import RequestFactory

from kuma.core.context_processors import next_url


def test_next_url_basic():
    path = "/one/two"
    request = RequestFactory().get(path)
    assert path == next_url(request)["next_url"]()


def test_next_url_querystring():
    path = "/one/two?something"
    request = RequestFactory().get(path)
    assert path == next_url(request)["next_url"]()


def test_next_url_with_next_querystring():
    path = "/one/two?next=/foo/bar"
    request = RequestFactory().get(path)
    assert next_url(request)["next_url"]() == "/foo/bar"


def test_next_url_with_next_querystring_but_remote():
    path = "/one/two?next=http://foo/bar"
    request = RequestFactory().get(path)
    assert next_url(request)["next_url"]() is None


def test_next_url_already_on_login_url(settings):
    request = RequestFactory().get(f"/en-US{settings.LOGIN_URL}")
    assert next_url(request)["next_url"]() is None
