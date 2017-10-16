from email.utils import parsedate
from time import gmtime

from ..models import User, UserBan

import pytest


@pytest.fixture()
def test_user(db):
    return User.objects.create(username='user', email='user@example.com')


@pytest.fixture()
def user_client(test_user, client):
    test_user.set_password('password')
    test_user.save()
    client.login(username='user', password='password')
    return client


def test_ban_middleware_anon_user(db, client):
    resp = client.get('/en-US/')
    assert resp.status_code == 200
    templates = [template.name for template in resp.templates]
    assert 'users/user_banned.html' not in templates
    assert not resp.has_header('Vary')


def test_ban_middleware_unbanned_user(user_client):
    resp = user_client.get('/en-US/')
    assert resp.status_code == 200
    templates = [template.name for template in resp.templates]
    assert 'users/user_banned.html' not in templates
    assert resp['Vary'] == 'Cookie'


def test_ban_middleware_banned_user(test_user, user_client, admin_user):
    UserBan.objects.create(user=test_user, by=admin_user,
                           reason='Banned by unit test.', is_active=True)
    resp = user_client.get('/en-US/')
    assert resp.status_code == 200
    templates = [template.name for template in resp.templates]
    assert 'users/user_banned.html' in templates
    assert parsedate(resp['Expires']) <= gmtime()
    assert not resp.has_header('Vary')
    never_cache = 'no-cache, no-store, must-revalidate, max-age=0'
    assert resp['Cache-Control'] == never_cache
