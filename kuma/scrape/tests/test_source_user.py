"""Tests for the UserSource class (/profiles/USERNAME)."""


from datetime import datetime

import pytest

from kuma.users.models import UserBan

from . import mock_requester, mock_storage
from ..sources import UserSource


@pytest.fixture
def complex_user(db, django_user_model):
    """A complex User record with social and other profile data."""
    user = django_user_model.objects.create(
        username="JillDeveloper",
        fullname="Jill Developer",
        email="jill@example.com",
        title="Web Developer",
        organization="Acme, Inc.",
        location="Springfield, USA",
        date_joined=datetime(1999, 1, 1, 10, 40, 23),
        twitter_url="http://twitter.com/jilldev1999",
        github_url="https://github.com/jilldev1999",
        stackoverflow_url="http://stackoverflow.com/users/1/jilldev1999",
        linkedin_url="http://www.linkedin.com/in/jilldev1999",
        pmo_url="https://people.mozilla.org/p/jilldev/",
    )
    return user


@pytest.mark.parametrize("email", ["", "jack@example.com"])
def test_gather_simple(email, simple_user, client):
    html = client.get(simple_user.get_absolute_url(), follow=True).content
    source = UserSource(simple_user.username, email=email, social=True)
    requester = mock_requester(content=html, status_code=200)
    storage = mock_storage(spec=["get_user", "save_user"])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    storage.get_user.assert_called_once_with(simple_user.username)
    expected_data = {
        "username": "JackDeveloper",
        "date_joined": datetime(2016, 11, 4, 9, 1),
    }
    if email:
        expected_data["email"] = email
    storage.save_user.assert_called_once_with(expected_data)


def test_gather_existing_user():
    source = UserSource("existing", social=True)
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=["get_user"])
    storage.get_user.return_value = {"username": "existing"}
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_NO


def test_gather_banned(simple_user, client):
    UserBan.objects.create(
        user=simple_user, by=simple_user, reason="Turning myself in."
    )
    user_path = "/en-US/profiles/" + simple_user.username
    result = client.get(user_path)
    source = UserSource(simple_user.username, force=True)
    requester = mock_requester(content=result.content, status_code=result.status_code)
    storage = mock_storage(spec=["save_user"])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    expected_data = {"username": simple_user.username, "banned": True}
    storage.save_user.assert_called_once_with(expected_data)


def test_gather_missing():
    source = UserSource("missing", force=True)
    requester = mock_requester(content="not found", status_code=404)
    storage = mock_storage()
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR


def test_extract_complex(complex_user, client):
    html = client.get(complex_user.get_absolute_url(), follow=True).content
    source = UserSource(complex_user.username)
    data = source.extract_data(html)
    expected_data = {
        "username": "JillDeveloper",
        "fullname": "Jill Developer",
        "title": "Web Developer",
        "organization": "Acme, Inc.",
        "location": "Springfield, USA",
        "date_joined": datetime(1999, 1, 1, 10, 40, 23),
    }
    assert data == expected_data


def test_extract_complex_social(complex_user, client):
    html = client.get(complex_user.get_absolute_url(), follow=True).content
    source = UserSource(complex_user.username, social=True)
    data = source.extract_data(html)
    expected_data = {
        "username": "JillDeveloper",
        "fullname": "Jill Developer",
        "title": "Web Developer",
        "organization": "Acme, Inc.",
        "location": "Springfield, USA",
        "twitter_url": "http://twitter.com/jilldev1999",
        "github_url": "https://github.com/jilldev1999",
        "stackoverflow_url": "http://stackoverflow.com/users/1/jilldev1999",
        "linkedin_url": "http://www.linkedin.com/in/jilldev1999",
        "pmo_url": "http://people.mozilla.org/u/jilldev/",
        "date_joined": datetime(1999, 1, 1, 10, 40, 23),
    }
    assert data == expected_data


def test_extract_irc(complex_user, client):
    complex_user.irc_nickname = "jilldev"
    complex_user.save()
    html = client.get(complex_user.get_absolute_url(), follow=True).content
    source = UserSource(complex_user.username, social=True)
    data = source.extract_data(html)
    assert data["irc_nickname"] == "jilldev"
