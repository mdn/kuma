

import pytest

from constance import config
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from kuma.users.models import User, UserBan

from ..fixture import FixtureLoader


def test_empty_fixtures():
    """A empty specification is OK, does nothing."""
    FixtureLoader({}).load()


@pytest.mark.django_db
def test_load_constance():
    """A fixture without dependencies is loaded."""
    spec = {
        'database.constance': [{
            'key': 'KUMASCRIPT_MAX_AGE', 'value': 321
        }]}
    FixtureLoader(spec).load()
    config._backend._cache = None  # Avoid cached config value
    assert config.KUMASCRIPT_MAX_AGE == 321


@pytest.mark.django_db
def test_load_group():
    """A fixture with existing to-many dependencies is loaded."""
    spec = {
        'auth.group': [{
            'name': 'Attachment Moderators',
            'permissions': [
                ['change_attachment']
            ]
        }],
        'auth.permission': [{
            'codename': 'change_attachment',
            'name': 'Can change attachment',
            'content_type': ['attachments', 'attachment']
        }],
        'contenttypes.contenttype': [{
            'app_label': 'attachments',
            'model': 'attachment',
        }]
    }
    ct_attachment = ContentType.objects.get(
        app_label='attachments', model='attachment')
    perm_attachment = Permission.objects.get(
        content_type=ct_attachment, codename='change_attachment')
    group_query = Group.objects.filter(name='Attachment Moderators')
    assert not group_query.exists()

    FixtureLoader(spec).load()

    group = group_query.get()
    assert list(group.permissions.all()) == [perm_attachment]


def test_underspecified_key_is_error():
    """A fixture must define all the natural key items."""
    spec = {
        'users.user': [{
            'email': 'email@example.com',
            'password': 'password',
        }]
    }
    with pytest.raises(ValueError) as error:
        FixtureLoader(spec)
    assert str(error.value) == 'users.user 0: Needs key "username"'


@pytest.mark.django_db
def test_relation_as_key():
    """A fixture with a relation as a key can be loaded."""
    spec = {
        'users.user': [{
            'username': 'admin',
            'is_staff': True
        }, {
            'username': 'spammer',
        }],
        'users.userban': [{
            'user': ['spammer'],
            'by': ['admin'],
            'reason': 'Spam'
        }]
    }
    FixtureLoader(spec).load()
    ban = UserBan.objects.get()
    assert ban.user.username == 'spammer'
    assert ban.by.username == 'admin'


@pytest.mark.django_db
def test_update_m2m_of_existing_instance():
    """Many-to-many relations of existing instances are updated."""
    user = User.objects.create(username='ironman')
    assert not user.groups.exists()
    spec = {
        'auth.group': [{
            'name': 'Avengers',
        }, {
            'name': 'Illuminati',
        }],
        'users.user': [{
            'username': 'ironman',
            'is_staff': True,
            'groups': [['Avengers'], ['Illuminati']]
        }]
    }
    FixtureLoader(spec).load()
    user.refresh_from_db()
    new_groups = list(sorted(user.groups.values_list('name', flat=True)))
    assert new_groups == ['Avengers', 'Illuminati']


def test_missing_relation_is_error():
    """An unspecified relation is detected, raises exception."""
    spec = {
        'users.user': [{
            'username': 'captain_america',
            'groups': [['SHIELD']]
        }]
    }
    with pytest.raises(RuntimeError) as error:
        FixtureLoader(spec).load()
    assert str(error.value) == 'Dependency block detected.'


@pytest.mark.django_db
def test_missing_key_relation_is_error():
    """An unspecified relation is detected, raises exception."""
    spec = {
        'users.user': [{
            'username': 'odin',
        }],
        'users.userban': [{
            'user': ['loki'],
            'by': ['odin'],
            'reason': 'Treason'
        }]
    }
    with pytest.raises(RuntimeError) as error:
        FixtureLoader(spec).load()
    assert str(error.value) == 'Dependency block detected.'


@pytest.mark.django_db
def test_user_password():
    """A user.password is hashed."""
    spec = {
        'users.user': [{
            'username': 'wagstaff',
            'password': 'swordfish'
        }]
    }
    FixtureLoader(spec).load()
    user = User.objects.get(username='wagstaff')
    assert user.check_password('swordfish')
