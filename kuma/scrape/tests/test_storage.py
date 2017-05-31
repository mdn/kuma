from __future__ import unicode_literals
from datetime import datetime

from taggit.models import Tag
import pytest

from kuma.scrape.storage import Storage


def test_safe_add_tags_new(simple_user):
    tag = 'profile:interest:testing'
    Storage().safe_add_tags([tag], Tag, simple_user.tags)
    assert list(simple_user.tags.names()) == [tag]


def test_safe_add_tags_existing(simple_user):
    tag = 'profile:expertise:existence'
    Tag.objects.create(name=tag)
    Storage().safe_add_tags([tag], Tag, simple_user.tags)
    assert list(simple_user.tags.names()) == [tag]


def test_safe_add_tags_case_mismatch(simple_user):
    tag = 'profile:interest:css'
    Tag.objects.create(name=tag)
    upper_tag = 'profile:interest:CSS'
    Storage().safe_add_tags([upper_tag], Tag, simple_user.tags)
    assert list(simple_user.tags.names()) == [tag]


@pytest.mark.django_db
def test_get_user_missing():
    assert Storage().get_user('missing') is None


def test_get_user_present(simple_user):
    user = Storage().get_user(simple_user.username)
    assert user == simple_user


@pytest.mark.django_db
def test_save_user(django_user_model):
    data = {
        'username': 'JoeDeveloper',
        'fullname': 'Joe Developer',
        'title': 'Web Developer',
        'organization': 'Acme, Inc.',
        'location': 'Springfield, USA',
        'irc_nickname': 'joedev',
        'interest': ['CSS', 'HTML', 'JavaScript'],
        'expertise': ['HTML'],
        'twitter_url': 'http://twitter.com/joedev1999',
        'github_url': 'https://github.com/joedev1999',
        'stackoverflow_url': 'http://stackoverflow.com/users/1/joedev1999',
        'linkedin_url': 'http://www.linkedin.com/in/joedev1999',
        'mozillians_url': 'http://mozillians.org/u/joedev/',
        'date_joined': datetime(1999, 1, 1, 10, 40, 23),
    }
    Storage().save_user(data)
    user = django_user_model.objects.get(username='JoeDeveloper')
    assert user.fullname == 'Joe Developer'
    assert user.title == 'Web Developer'
    assert user.organization == 'Acme, Inc.'
    assert user.location == 'Springfield, USA'
    assert user.irc_nickname == 'joedev'
    assert user.twitter_url == 'http://twitter.com/joedev1999'
    assert user.github_url == 'https://github.com/joedev1999'
    assert user.stackoverflow_url == (
        'http://stackoverflow.com/users/1/joedev1999')
    assert user.linkedin_url == 'http://www.linkedin.com/in/joedev1999'
    assert user.mozillians_url == 'http://mozillians.org/u/joedev/'
    assert user.date_joined == datetime(1999, 1, 1, 10, 40, 23)
    tags = sorted(user.tags.names())
    expected_tags = [
        'profile:expertise:HTML',
        'profile:interest:CSS',
        'profile:interest:HTML',
        'profile:interest:JavaScript',
    ]
    assert tags == expected_tags


@pytest.mark.django_db
def test_save_user_banned(django_user_model):
    data = {
        'username': 'banned',
        'date_joined': datetime(2016, 12, 19),
        'banned': True
    }
    Storage().save_user(data)
    user = django_user_model.objects.get(username='banned')
    assert user.bans.count() == 1
    ban = user.bans.first()
    assert ban.by == user
    assert ban.reason == 'Ban detected by scraper'
