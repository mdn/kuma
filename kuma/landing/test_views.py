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
def test_robots_enabled(client, db, settings, allowed):
    settings.ALLOW_ROBOTS = allowed
    response = client.get(reverse('robots_txt'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain'
    content = ''.join(response.streaming_content)
    if allowed:
        assert 'Sitemap: ' in content
    else:
        assert 'Disallow: /' in content
