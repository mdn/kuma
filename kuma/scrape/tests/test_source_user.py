# -*- coding: utf-8 -*-
"""Tests for the UserSource class (/profiles/USERNAME)."""
from __future__ import unicode_literals
from datetime import datetime

import pytest

from kuma.scrape.sources import UserSource
from . import mock_requester, mock_storage


@pytest.fixture
def complex_user(db, django_user_model):
    """A complex User record with social and other profile data."""
    user = django_user_model.objects.create(
        username='JillDeveloper',
        fullname='Jill Developer',
        email='jill@example.com',
        title='Web Developer',
        organization='Acme, Inc.',
        location='Springfield, USA',
        date_joined=datetime(1999, 1, 1, 10, 40, 23),
        twitter_url='http://twitter.com/jilldev1999',
        github_url='https://github.com/jilldev1999',
        stackoverflow_url='http://stackoverflow.com/users/1/jilldev1999',
        linkedin_url='http://www.linkedin.com/in/jilldev1999',
        mozillians_url='http://mozillians.org/u/jilldev/')
    user.tags.set_ns('profile:interest:', 'JavaScript', 'HTML', 'CSS')
    user.tags.set_ns('profile:expertise:', 'HTML')
    return user


@pytest.fixture
def complex_user_html(complex_user, client):
    """The profile HTML for a complex user."""
    user_path = '/en-US/profiles/' + complex_user.username
    return client.get(user_path).content


@pytest.fixture
def irc_user(complex_user):
    """A complex User record that also has an IRC nickname."""
    complex_user.irc_nickname = 'jilldev'
    complex_user.save()
    return complex_user


@pytest.fixture
def irc_user_html(irc_user, client):
    """The profile HTML for the user with an IRC nickname."""
    user_path = '/en-US/profiles/' + irc_user.username
    return client.get(user_path).content


@pytest.mark.parametrize("email", ['', 'jack@example.com'])
def test_gather_simple(email, simple_user, simple_user_html):
    source = UserSource(simple_user.username, email=email, social=True)
    requester = mock_requester(content=simple_user_html, status_code=200)
    storage = mock_storage(spec=['get_user', 'save_user'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    storage.get_user.assert_called_once_with(simple_user.username)
    expected_data = {
        'username': 'JackDeveloper',
        'date_joined': datetime(2016, 11, 4, 9, 1)
    }
    if email:
        expected_data['email'] = email
    storage.save_user.assert_called_once_with(expected_data)


def test_gather_existing_user():
    source = UserSource('existing', social=True)
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=['get_user'])
    storage.get_user.return_value = {'username': 'existing'}
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_NO


def test_gather_banned():
    source = UserSource('banned', force=True)
    requester = mock_requester(content="banned", status_code=403)
    storage = mock_storage(spec=['save_user'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    expected_data = {
        'username': 'banned',
        'banned': True
    }
    storage.save_user.assert_called_once_with(expected_data)


def test_gather_missing():
    source = UserSource('missing', force=True)
    requester = mock_requester(content="not found", status_code=404)
    storage = mock_storage()
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR


def test_extract_complex(complex_user, complex_user_html):
    source = UserSource(complex_user.username)
    data = source.extract_data(complex_user_html)
    expected_data = {
        'username': 'JillDeveloper',
        'fullname': 'Jill Developer',
        'title': 'Web Developer',
        'organization': 'Acme, Inc.',
        'location': 'Springfield, USA',
        'interest': ['CSS', 'HTML', 'JavaScript'],
        'expertise': ['HTML'],
        'date_joined': datetime(1999, 1, 1, 10, 40, 23),
    }
    assert data == expected_data


def test_extract_complex_social(complex_user, complex_user_html):
    source = UserSource(complex_user.username, social=True)
    data = source.extract_data(complex_user_html)
    expected_data = {
        'username': 'JillDeveloper',
        'fullname': 'Jill Developer',
        'title': 'Web Developer',
        'organization': 'Acme, Inc.',
        'location': 'Springfield, USA',
        'interest': ['CSS', 'HTML', 'JavaScript'],
        'expertise': ['HTML'],
        'twitter_url': 'http://twitter.com/jilldev1999',
        'github_url': 'https://github.com/jilldev1999',
        'stackoverflow_url': 'http://stackoverflow.com/users/1/jilldev1999',
        'linkedin_url': 'http://www.linkedin.com/in/jilldev1999',
        'mozillians_url': 'http://mozillians.org/u/jilldev/',
        'date_joined': datetime(1999, 1, 1, 10, 40, 23),
    }
    assert data == expected_data


def test_extract_irc(irc_user, irc_user_html):
    source = UserSource(irc_user.username, social=True)
    data = source.extract_data(irc_user_html)
    assert data['irc_nickname'] == irc_user.irc_nickname
