from kuma.core.tests import assert_shared_cache_header
from kuma.core.urlresolvers import reverse


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
