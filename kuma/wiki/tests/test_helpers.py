import pytest

from ..templatetags.jinja_helpers import absolutify


@pytest.mark.parametrize(
    "path,abspath",
    (
        ("", "https://testserver/"),
        ("/", "https://testserver/"),
        ("//", "https://testserver/"),
        ("/foo/bar", "https://testserver/foo/bar"),
        ("http://domain.com", "http://domain.com"),
        ("/woo?var=value", "https://testserver/woo?var=value"),
        ("/woo?var=value#fragment", "https://testserver/woo?var=value#fragment"),
    ),
)
def test_absolutify(settings, path, abspath):
    """absolutify adds the current site to paths without domains."""
    settings.SITE_URL = "https://testserver"
    assert absolutify(path) == abspath


def test_absolutify_dev(settings):
    """absolutify uses http in development."""
    settings.SITE_URL = "http://localhost:8000"
    assert absolutify("") == "http://localhost:8000/"
