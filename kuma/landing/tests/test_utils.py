import pytest

from django.conf import settings

from ..utils import favicon_url


@pytest.mark.parametrize(
    "domain, expected",
    (
        ("testserver", "/static/img/favicon32-local.png"),
        (settings.PRODUCTION_DOMAIN, "/static/img/favicon32.png"),
        (settings.STAGING_DOMAIN, "/static/img/favicon32-staging.png"),
    ),
)
def test_favicon_url(settings, domain, expected):
    settings.DOMAIN = domain
    settings.ALLOWED_HOSTS.append(domain)
    settings.STATIC_URL = "/static/"
    url = favicon_url()
    assert url == expected
