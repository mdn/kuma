from urllib.parse import urlparse

import pytest
from django.core.cache import cache

from kuma.core.tests import (
    assert_no_cache_header,
    assert_shared_cache_header,
)
from kuma.core.urlresolvers import reverse


@pytest.fixture()
def cleared_cache():
    cache.clear()
    yield cache
    cache.clear()


@pytest.mark.parametrize("mode", ["maintenance", "normal"])
def test_maintenance_mode(db, client, settings, mode):
    url = reverse("maintenance_mode")
    settings.MAINTENANCE_MODE = mode == "maintenance"
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    if settings.MAINTENANCE_MODE:
        assert response.status_code == 200
        assert "landing/maintenance-mode.html" in [t.name for t in response.templates]
    else:
        assert response.status_code == 302
        assert "Location" in response
        assert urlparse(response["Location"]).path == "/en-US/"
    assert_no_cache_header(response)


def test_robots_not_allowed(client):
    """By default, robots.txt shows that robots are not allowed."""
    response = client.get(reverse("robots_txt"))
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response["Content-Type"] == "text/plain"
    content = response.content
    assert b"Sitemap: " not in content
    assert b"Disallow: /\n" in content
    assert b"Disallow: /api/\n" not in content


def test_robots_allowed_main_website(client, settings):
    """On the main website, allow robots with restrictions."""
    host = "main.mdn.moz.works"
    settings.ALLOW_ROBOTS_WEB_DOMAINS = [host]
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(reverse("robots_txt"), HTTP_HOST=host)
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response["Content-Type"] == "text/plain"
    content = response.content
    assert b"Sitemap: " in content
    assert b"Disallow: /\n" not in content
    assert b"Disallow: /api/\n" in content


def test_robots_all_allowed_wiki_website(client, settings):
    """On the wiki website, allow robots with NO restrictions."""
    host = "main.mdn.moz.works"
    wiki_host = "wiki." + host
    settings.WIKI_HOST = wiki_host
    settings.ALLOWED_HOSTS = [host, wiki_host]
    settings.ALLOW_ROBOTS_WEB_DOMAINS = [host, wiki_host]
    response = client.get(reverse("robots_txt"), HTTP_HOST=wiki_host)
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response["Content-Type"] == "text/plain"
    content = response.content
    assert b"Sitemap: " in content
    assert b"Disallow:\n" in content
    assert b"Disallow: /" not in content


def test_robots_allowed_main_attachment_host(client, settings):
    """On the main attachment host, allow robots without restrictions."""
    host = "samples.mdn.moz.works"
    settings.ALLOW_ROBOTS_DOMAINS = [host]
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(reverse("robots_txt"), HTTP_HOST=host)
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response["Content-Type"] == "text/plain"
    content = response.content
    assert content == b""


def test_favicon_ico(client, settings):
    settings.STATIC_URL = "/static/"
    response = client.get("/favicon.ico")
    assert response.status_code == 302
    assert_shared_cache_header(response)
    assert response["Location"] == "/static/img/favicon32-local.png"
