from __future__ import unicode_literals

import mock
import pytest
from django.core.cache import cache
from django.utils.six.moves.urllib.parse import urlparse
from ratelimit.exceptions import Ratelimited

from kuma.core.tests import assert_no_cache_header, assert_shared_cache_header
from kuma.core.urlresolvers import reverse


@pytest.fixture()
def cleared_cache():
    cache.clear()
    yield cache
    cache.clear()


def test_contribute_json(client, db):
    response = client.get(reverse('contribute_json'))
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response['Content-Type'].startswith('application/json')


@pytest.mark.parametrize('case', ('DOMAIN', 'BETA_HOST', 'WIKI_HOST'))
def test_home(client, db, host_settings, case):
    host = getattr(host_settings, case)
    response = client.get(reverse('home', locale='en-US'), HTTP_HOST=host)
    assert response.status_code == 200
    assert_shared_cache_header(response)
    if case in ('DOMAIN', 'WIKI_HOST'):
        expected_template = 'landing/homepage.html'
    else:
        expected_template = 'landing/react_homepage.html'
    assert expected_template in (t.name for t in response.templates)


@mock.patch('kuma.landing.views.render')
def test_home_when_rate_limited(mock_render, client, db):
    """
    Cloudfront CDN's don't cache 429's, but let's test this anyway.
    """
    mock_render.side_effect = Ratelimited()
    response = client.get(reverse('home'))
    assert response.status_code == 429
    assert_no_cache_header(response)


@pytest.mark.parametrize('mode', ['maintenance', 'normal'])
def test_maintenance_mode(db, client, settings, mode):
    url = reverse('maintenance_mode')
    settings.MAINTENANCE_MODE = (mode == 'maintenance')
    response = client.get(url)
    if settings.MAINTENANCE_MODE:
        assert response.status_code == 200
        assert ('landing/maintenance-mode.html' in
                [t.name for t in response.templates])
    else:
        assert response.status_code == 302
        assert 'Location' in response
        assert urlparse(response['Location']).path == '/en-US/'
    assert_no_cache_header(response)


def test_promote_buttons(client, db):
    response = client.get(reverse('promote_buttons'), follow=True)
    assert response.status_code == 200
    assert_shared_cache_header(response)


def test_robots_not_allowed(client):
    """By default, robots.txt shows that robots are not allowed."""
    response = client.get(reverse('robots_txt'))
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response['Content-Type'] == 'text/plain'
    content = response.content
    assert b'Sitemap: ' not in content
    assert b'Disallow: /\n' in content
    assert b'Disallow: /admin/\n' not in content


def test_robots_allowed_main_website(client, settings):
    """On the main website, allow robots with restrictions."""
    host = 'main.mdn.moz.works'
    settings.ALLOW_ROBOTS_WEB_DOMAINS = [host]
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(reverse('robots_txt'), HTTP_HOST=host)
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response['Content-Type'] == 'text/plain'
    content = response.content
    assert b'Sitemap: ' in content
    assert b'Disallow: /\n' not in content
    assert b'Disallow: /admin/\n' in content


def test_robots_allowed_main_attachment_host(client, settings):
    """On the main attachment host, allow robots without restrictions."""
    host = 'samples.mdn.moz.works'
    settings.ALLOW_ROBOTS_DOMAINS = [host]
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(reverse('robots_txt'), HTTP_HOST=host)
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response['Content-Type'] == 'text/plain'
    content = response.content
    assert content == b''


def test_favicon_ico(client, settings):
    settings.STATIC_URL = '/static/'
    response = client.get('/favicon.ico')
    assert response.status_code == 302
    assert_shared_cache_header(response)
    assert response['Location'] == '/static/img/favicon32-local.png'
