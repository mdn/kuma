import pytest

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


@pytest.mark.parametrize('allowed', [True, False])
@pytest.mark.parametrize(
    'host', [None, 'ATTACHMENT_HOST', 'ATTACHMENT_ORIGIN'])
def test_robots(client, db, settings, host, allowed):
    settings.ALLOW_ROBOTS = allowed
    settings.ATTACHMENT_HOST = 'demos'
    settings.ATTACHMENT_ORIGIN = 'demos-origin'
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    headers = {'HTTP_HOST': getattr(settings, host)} if host else {}
    response = client.get(reverse('robots_txt'), **headers)
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain'
    content = ''.join(response.streaming_content)
    if host or not allowed:
        assert 'Disallow: /' in content
    else:
        assert 'Sitemap: ' in content


def test_favicon_ico(client):
    response = client.get('favicon.ico')
    assert response.status_code == 302
    assert response['Location'].endswith('static/img/favicon.ico')
