import json
from unittest import mock

import pytest
from django.db import DatabaseError
from django.urls import reverse

from kuma.core.tests import assert_no_cache_header
from kuma.users.models import User


@pytest.fixture
def mock_search_count():
    with mock.patch("elasticsearch_dsl.connections.Elasticsearch") as search:
        instance = search()
        instance.cluster.health.return_value = {"status": "pink"}
        instance.count.return_value = {"count": 90}
        yield instance


@pytest.mark.parametrize("http_method", ["put", "post", "delete", "options"])
@pytest.mark.parametrize("endpoint", ["liveness", "readiness", "status"])
def test_disallowed_methods(client, http_method, endpoint):
    """Alternate HTTP methods are not allowed."""
    url = reverse("health.{}".format(endpoint))
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.parametrize("http_method", ["get", "head"])
@pytest.mark.parametrize("endpoint", ["liveness", "readiness"])
def test_liveness_and_readiness(db, client, http_method, endpoint):
    url = reverse("health.{}".format(endpoint))
    response = getattr(client, http_method)(url)
    assert response.status_code == 204
    assert_no_cache_header(response)


@mock.patch("kuma.wiki.models.Document.objects")
def test_readiness_with_db_error(mock_manager, db, client):
    mock_manager.filter.side_effect = DatabaseError("fubar")
    response = client.get(reverse("health.readiness"))
    assert response.status_code == 503
    assert "fubar" in response.reason_phrase
    assert_no_cache_header(response)


@pytest.fixture
def mock_document_objects_count():
    with mock.patch("kuma.health.views.Document") as model:
        model.objects = mock.Mock(spec_set=["count"])
        model.objects.count.return_value = 100
        yield model.objects.count


@pytest.fixture
def mock_user_objects_filter():
    usernames = [
        "test-super",
        "test-moderator",
        "test-new",
        "test-banned",
        "viagra-test-123",
    ]
    users = []
    for username in usernames:
        user = User(username=username)
        user.set_password("test-password")
        users.append(user)
    with mock.patch("kuma.health.views.User") as model:
        model.objects = mock.Mock(spec_set=["only"])
        model.objects.only.return_value = mock.Mock(spec_set=["filter"])
        filter_func = model.objects.only.return_value.filter
        filter_func.return_value = users
        yield filter_func


@pytest.fixture
def mock_status_externals(
    mock_document_objects_count,
    mock_search_count,
    mock_user_objects_filter,
):
    yield {
        "document": mock_document_objects_count,
        "search": mock_search_count,
        "test_users": mock_user_objects_filter,
    }


def test_status(client, settings, mock_status_externals):
    """The status JSON reflects the test environment."""
    # Normalize to docker development settings
    dev_settings = {
        "ALLOWED_HOSTS": ["*"],
        "ATTACHMENT_HOST": "demos:8000",
        "ATTACHMENT_ORIGIN": "demos:8000",
        "ATTACHMENTS_AWS_S3_CUSTOM_URL": "https://media.prod.mdn.mozit.cloud",
        "DEBUG": False,
        "INTERACTIVE_EXAMPLES_BASE": "https://interactive-examples.mdn.mozilla.net",
        "MAINTENANCE_MODE": False,
        "PROTOCOL": "http://",
        "REVISION_HASH": "3f45719d45f15da73ccc15747c28b80ccc8dfee5",
        "SITE_URL": "http://mdn.localhost:8000",
        "STATIC_URL": "/static/",
    }
    for name, value in dev_settings.items():
        setattr(settings, name, value)

    url = reverse("health.status")
    response = client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    assert response["Content-Type"] == "application/json"
    data = json.loads(response.content)
    assert sorted(data.keys()) == ["request", "services", "settings", "version"]
    assert data["settings"] == dev_settings
    assert data["request"] == {
        "host": "testserver",
        "is_secure": False,
        "scheme": "http",
        "url": "http://testserver/_kuma_status.json",
    }
    assert sorted(data["services"].keys()) == [
        "database",
        "search",
        "test_accounts",
    ]
    assert data["services"]["database"] == {
        "available": True,
        "populated": True,
        "document_count": 100,
    }
    assert data["services"]["search"] == {
        "available": True,
        "populated": True,
        "count": 90,
        "health": {"status": "pink"},
    }
    assert data["services"]["test_accounts"] == {
        "available": True,
    }
    assert data["version"] == 1


STATUS_SETTINGS_CASES = {
    "ALLOWED_HOSTS": ["localhost", "testserver"],
    "ATTACHMENT_HOST": "attachments.test.moz.works",
    "ATTACHMENT_ORIGIN": "attachments-origin.test.moz.works",
    "DEBUG": True,
    "INTERACTIVE_EXAMPLES_BASE": "https://interactive-examples.mdn.moz.works",
    "MAINTENANCE_MODE": True,
    "REVISION_HASH": "NEW_VALUE",
    "SITE_URL": "https://mdn.moz.works",
    "STATIC_URL": "https://cdn.test.moz.works/static/",
}


@pytest.mark.parametrize(
    "name,new_value", STATUS_SETTINGS_CASES.items(), ids=list(STATUS_SETTINGS_CASES)
)
def test_status_settings_change(
    name, new_value, client, settings, mock_status_externals
):
    """The status JSON reflects the current Django settings."""
    assert getattr(settings, name) != new_value
    setattr(settings, name, new_value)

    url = reverse("health.status")
    response = client.get(url)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["settings"][name] == new_value


@pytest.mark.parametrize("value", ("https://", "http://"))
def test_status_settings_protocol(value, client, settings, mock_status_externals):
    """
    The status JSON reflects the PROTOCOL setting

    In local dev, this is http, but it is https in TravisCI, so it is not a
    good fit for test_status_settings_change
    """
    settings.PROTOCOL = value
    url = reverse("health.status")
    response = client.get(url)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["settings"]["PROTOCOL"] == value


def test_status_failed_database(client, mock_status_externals):
    """The status JSON shows if the database is unavailable."""
    mock_status_externals["document"].side_effect = DatabaseError("fubar")
    url = reverse("health.status")
    response = client.get(url)
    data = json.loads(response.content)
    assert data["services"]["database"] == {
        "available": False,
        "populated": False,
        "document_count": 0,
    }


def test_status_empty_database(client, mock_status_externals):
    """The status JSON shows if the database is empty."""
    mock_status_externals["document"].return_value = 0
    url = reverse("health.status")
    response = client.get(url)
    data = json.loads(response.content)
    assert data["services"]["database"] == {
        "available": True,
        "populated": False,
        "document_count": 0,
    }


def test_status_test_acccounts_no_database(client, mock_status_externals):
    """The status JSON shows accounts unavailable if no database."""
    mock_status_externals["test_users"].side_effect = DatabaseError("wat")
    url = reverse("health.status")
    response = client.get(url)
    data = json.loads(response.content)
    assert data["services"]["test_accounts"] == {
        "available": False,
    }


def test_status_test_acccounts_unavailable(client, mock_status_externals):
    """The status JSON shows if the test accounts are unavailable."""
    mock_status_externals["test_users"].return_value = []
    url = reverse("health.status")
    response = client.get(url)
    data = json.loads(response.content)
    assert data["services"]["test_accounts"] == {
        "available": False,
    }


def test_status_test_acccounts_one_missing(client, mock_status_externals):
    """The status JSON shows if there is a missing test account."""
    mock_status_externals["test_users"].return_value.pop()
    url = reverse("health.status")
    response = client.get(url)
    data = json.loads(response.content)
    assert data["services"]["test_accounts"] == {
        "available": False,
    }


def test_status_test_acccounts_wrong_password(client, mock_status_externals):
    """The status JSON shows if a test account has the wrong password."""
    user = mock_status_externals["test_users"].return_value[0]
    user.set_password("not_the_password")
    url = reverse("health.status")
    response = client.get(url)
    data = json.loads(response.content)
    assert data["services"]["test_accounts"] == {
        "available": False,
    }
