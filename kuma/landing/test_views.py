import pytest

from kuma.core.urlresolvers import reverse


@pytest.fixture()
def robots(tmpdir):
    path = tmpdir.realpath()
    robots_file = tmpdir.join('robots.txt')
    robots_go_away_file = tmpdir.join('robots-go-away.txt')
    robots_file.write_text(u'robots: {}'.format(path), 'utf8')
    robots_go_away_file.write_text(u'robots-go-away: {}'.format(path), 'utf8')
    return {
        'tmpdir': tmpdir,
        'robots': robots_file.read_text('utf8'),
        'robots-go-away': robots_go_away_file.read_text('utf8'),
    }


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


@pytest.mark.parametrize('allowed', [True, False])
def test_robots_root(client, db, settings, robots, allowed):
    settings.ROBOTS_ROOT = robots['tmpdir'].realpath()
    settings.ALLOW_ROBOTS = allowed
    response = client.get(reverse('robots_txt'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain'
    content = ''.join(response.streaming_content)
    if allowed:
        assert robots['robots'] in content
    else:
        assert robots['robots-go-away'] in content
