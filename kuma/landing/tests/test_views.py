from django.utils.six.moves.urllib.parse import urlparse
from ratelimit.exceptions import Ratelimited
import mock
import pytest

from kuma.core.urlresolvers import reverse


def test_contribute_json(client, db):
    response = client.get(reverse('contribute_json'))
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']
    assert response['Content-Type'].startswith('application/json')


def test_home(client, db):
    response = client.get(reverse('home'), follow=True)
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']


@mock.patch('kuma.landing.views.render')
def test_home_when_rate_limited(mock_render, client, db):
    """
    Cloudfront CDN's don't cache 429's, but let's test this anyway.
    """
    mock_render.side_effect = Ratelimited()
    response = client.get(reverse('home', locale='en-US'))
    assert response.status_code == 429
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


@pytest.mark.parametrize('mode', ['maintenance', 'normal'])
def test_maintenance_mode(db, client, settings, mode):
    url = reverse('maintenance_mode', locale='en-US')
    settings.MAINTENANCE_MODE = (mode == 'maintenance')
    response = client.get(url)
    if settings.MAINTENANCE_MODE:
        assert response.status_code == 200
        assert ('landing/maintenance-mode.html' in
                [t.name for t in response.templates])
    else:
        assert response.status_code == 302
        assert 'Location' in response
        assert urlparse(response['Location']).path == '/'
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


def test_promote_buttons(client, db):
    response = client.get(reverse('promote_buttons'), follow=True)
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']


def test_robots_not_allowed(client):
    """By default, robots.txt shows that robots are not allowed."""
    response = client.get(reverse('robots_txt'))
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']
    assert response['Content-Type'] == 'text/plain'
    content = response.content
    assert 'Sitemap: ' not in content
    assert 'Disallow: /\n' in content
    assert 'Disallow: /admin/\n' not in content


def test_robots_allowed_main_website(client, settings):
    """On the main website, allow robots with restrictions."""
    host = 'main.mdn.moz.works'
    settings.ALLOW_ROBOTS_WEB_DOMAINS = [host]
    response = client.get(reverse('robots_txt'), HTTP_HOST=host)
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']
    assert response['Content-Type'] == 'text/plain'
    content = response.content
    assert 'Sitemap: ' in content
    assert 'Disallow: /\n' not in content
    assert 'Disallow: /admin/\n' in content


def test_robots_allowed_main_attachment_host(client, settings):
    """On the main attachment host, allow robots without restrictions."""
    host = 'samples.mdn.moz.works'
    settings.ALLOW_ROBOTS_DOMAINS = [host]
    response = client.get(reverse('robots_txt'), HTTP_HOST=host)
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']
    assert response['Content-Type'] == 'text/plain'
    content = response.content
    assert content == ''


def test_favicon_ico(client):
    response = client.get('favicon.ico')
    assert response.status_code == 302
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']
    assert response['Location'].endswith('static/img/favicon.ico')
