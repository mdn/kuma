from kuma.core.urlresolvers import reverse


def test_contribute_json(client, db):
    response = client.get(reverse('contribute_json'))
    assert response.status_code == 200
    assert response['Content-Type'].startswith('application/json')


def test_home(client, db):
    response = client.get(reverse('home'), follow=True)
    assert response.status_code == 200


def test_promote_buttons(client, db):
    response = client.get(reverse('promote_buttons'), follow=True)
    assert response.status_code == 200


def test_robots_not_allowed(client):
    """By default, robots.txt shows that robots are not allowed."""
    response = client.get(reverse('robots_txt'))
    assert response.status_code == 200
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
    assert response['Content-Type'] == 'text/plain'
    content = response.content
    assert content == ''


def test_favicon_ico(client):
    response = client.get('favicon.ico')
    assert response.status_code == 302
    assert response['Location'].endswith('static/img/favicon.ico')
