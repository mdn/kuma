import copy
from urllib.parse import urlencode

import pytest

from kuma.core.urlresolvers import reverse
from kuma.users.models import UserProfile


@pytest.mark.django_db
def test_bookmarked_anonymous(client):
    response = client.get(reverse("api-v1:collections"))
    assert response.status_code == 401
    assert "Unauthorized" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_is_bookmarked_signed_in(user_client, wiki_user):
    url = reverse("api-v1:collections")
    response = user_client.get(url)
    assert response.status_code == 200

    UserProfile.objects.create(user=wiki_user)
    response = user_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_is_bookmarked_signed_in_subscriber(subscriber_client):
    url = reverse("api-v1:collections")
    response = subscriber_client.get(url, {"url": "some junk"})
    assert response.status_code == 422
    assert "invalid collection item url" in response.content.decode("utf-8")

    response = subscriber_client.get(url, {"url": "/not/a/mdny/url"})
    assert response.status_code == 422
    assert "invalid collection item url" in response.content.decode("utf-8")

    response = subscriber_client.get(url, {"url": "/docs/://ftphack"})
    assert response.status_code == 422
    assert "invalid collection item url" in response.content.decode("utf-8")

    response = subscriber_client.get(url, {"url": "/en-US/docs/Web"})
    assert response.status_code == 200
    # It's NOT been toggled yet
    assert response.json()["bookmarked"] is None
    assert response.json()["csrfmiddlewaretoken"]


@pytest.mark.django_db
def test_toggle_bookmarked(subscriber_client, mock_requests, settings):
    doc_data = {"doc": {"title": "Web", "mdn_url": "/en-US/docs/Web"}}

    mock_requests.register_uri(
        "GET", settings.BOOKMARKS_BASE_URL + "/en-US/docs/Web/index.json", json=doc_data
    )

    url = reverse("api-v1:collections")
    get_url = f'{url}?{urlencode({"url": "/en-US/docs/Web"})}'
    response = subscriber_client.post(get_url)
    assert response.status_code == 201

    response = subscriber_client.get(get_url)
    assert response.status_code == 200
    assert response.json()["bookmarked"]["id"]
    initial_id = response.json()["bookmarked"]["id"]
    assert response.json()["bookmarked"]["created"]
    assert response.json()["csrfmiddlewaretoken"]

    # Now toggle it off
    response = subscriber_client.post(get_url)
    assert response.status_code == 201

    # Soft deleted
    response = subscriber_client.post(get_url, {"delete": True})
    assert response.status_code == 200
    assert response.json()["ok"]

    # Not in response
    response = subscriber_client.get(get_url)
    assert response.status_code == 200
    assert not response.json()["bookmarked"]

    # And undo the soft-delete
    response = subscriber_client.post(get_url)
    assert response.status_code == 201

    # Should return with the same ID as before
    response = subscriber_client.get(get_url)
    assert response.status_code == 200
    response = subscriber_client.get(get_url)
    assert response.status_code == 200
    assert response.json()["bookmarked"]["id"] == initial_id

    # Case sensitive too
    response = subscriber_client.get(get_url.replace("en-US", "EN-us"))
    assert response.status_code == 200
    assert response.json()["bookmarked"]


@pytest.mark.django_db
def test_bookmarks_anonymous(client):
    response = client.get(reverse("api-v1:collections"))
    assert response.status_code == 401
    assert "Unauthorized" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_bookmarks_signed_in_subscriber(subscriber_client):
    url = reverse("api-v1:collections")
    response = subscriber_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0
    assert response.json()["metadata"]["total"] == 0
    assert response.json()["metadata"]["page"] == 1
    assert response.json()["metadata"]["per_page"] > 0

    # Try to mess with the `page` and `per_page`
    response = subscriber_client.get(url, {"page": "xxx"})
    assert response.status_code == 422
    assert "type_error.integer" in response.content.decode("utf-8")
    response = subscriber_client.get(url, {"page": "-1"})
    assert response.status_code == 422
    assert "value_error.number.not_gt" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_bookmarks_pagination(subscriber_client, mock_requests, settings):
    base_doc_data = {
        "doc": {
            "body": "BIG",
            "toc": "BIG",
            "sidebarHTML": "BIG",
            "other_translations": ["BIG"],
            "flaws": {"also": "BIG"},
            "mdn_url": "/en-US/docs/Web/Doc0",
            "title": "Document 0",
            "locale": "en-US",
            "parents": [
                {"uri": "/en-US/docs/Web", "title": "Web"},
                {"uri": "/en-US/docs/Web/Doc0", "title": "Document 0"},
            ],
        }
    }

    def create_doc_data(mdn_url, title):
        clone = copy.deepcopy(base_doc_data)
        clone["doc"]["title"] = title
        clone["doc"]["mdn_url"] = mdn_url
        clone["doc"]["parents"][-1]["title"] = title
        clone["doc"]["parents"][-1]["uri"] = mdn_url
        return clone

    url = reverse("api-v1:collections")

    for i in range(1, 21):
        mdn_url = f"/en-US/docs/Web/Doc{i}"
        doc_absolute_url = settings.BOOKMARKS_BASE_URL + mdn_url + "/index.json"
        print(doc_absolute_url)
        mock_requests.register_uri(
            "GET", doc_absolute_url, json=create_doc_data(mdn_url, f"Doc {i}")
        )
        get_url = f'{url}?{urlencode({"url": mdn_url})}'
        print(get_url)
        response = subscriber_client.post(get_url)
        print(response)
        assert response.status_code == 201, response.json()

    # Add one extra but then delete it
    i += 1
    mdn_url = f"/en-US/docs/Web/Doc{i}"
    doc_absolute_url = settings.BOOKMARKS_BASE_URL + mdn_url + "/index.json"
    mock_requests.register_uri(
        "GET", doc_absolute_url, json=create_doc_data(mdn_url, f"Doc {i}")
    )
    get_url = f'{url}?{urlencode({"url": mdn_url})}'
    response = subscriber_client.post(get_url)
    assert response.status_code == 201
    response = subscriber_client.post(get_url, {'delete': 1})
    assert response.status_code == 200

    response = subscriber_client.get(url, {"per_page": "5"})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 5
    assert response.json()["metadata"]["total"] == 20
    assert response.json()["metadata"]["page"] == 1
    assert response.json()["metadata"]["per_page"] == 5

    response = subscriber_client.get(url, {"per_page": "5", "page": "2"})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 5
    assert response.json()["metadata"]["total"] == 20
    assert response.json()["metadata"]["page"] == 2
    assert response.json()["metadata"]["per_page"] == 5


def test_undo_bookmark(subscriber_client, mock_requests, settings):
    def create_doc_data(mdn_url, title):
        base_doc_data = {
            "doc": {
                "body": "BIG",
                "toc": "BIG",
                "sidebarHTML": "BIG",
                "other_translations": ["BIG"],
                "flaws": {"also": "BIG"},
                "mdn_url": "/en-US/docs/Web/Doc0",
                "title": "Document 0",
                "locale": "en-US",
                "parents": [
                    {"uri": "/en-US/docs/Web", "title": "Web"},
                    {"uri": "/en-US/docs/Web/Doc0", "title": "Document 0"},
                ],
            }
        }
        clone = copy.deepcopy(base_doc_data)
        clone["doc"]["title"] = title
        clone["doc"]["mdn_url"] = mdn_url
        clone["doc"]["parents"][-1]["title"] = title
        clone["doc"]["parents"][-1]["uri"] = mdn_url
        return clone

    mock_requests.register_uri(
        "GET",
        settings.BOOKMARKS_BASE_URL + "/en-US/docs/Foo/index.json",
        json=create_doc_data("/en-US/docs/Foo", "Foo!"),
    )
    mock_requests.register_uri(
        "GET",
        settings.BOOKMARKS_BASE_URL + "/en-US/docs/Bar/index.json",
        json=create_doc_data("/en-US/docs/Bar", "Bar!"),
    )
    mock_requests.register_uri(
        "GET",
        settings.BOOKMARKS_BASE_URL + "/en-US/docs/Buzz/index.json",
        json=create_doc_data("/en-US/docs/Buzz", "Buzz!"),
    )

    url = reverse("api-v1:collections")

    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Foo"})}'
        ).status_code
        == 201
    )

    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Bar"})}'
        ).status_code
        == 201
    )

    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Buzz"})}'
        ).status_code
        == 201
    )

    response = subscriber_client.get(url)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 3
    assert [x["url"] for x in items] == [
        # The one that was bookmarked last
        "/en-US/docs/Buzz",
        # The one that was bookmarked second
        "/en-US/docs/Bar",
        # The one that was bookmarked first
        "/en-US/docs/Foo",
    ]
    # Suppose you decide to un-bookmark the first one.
    response = subscriber_client.post(
        f'{url}?{urlencode({"url": "/en-US/docs/Foo"})}', {"delete": True}
    )
    assert response.status_code == 200

    # Check that it disappears from the listing
    response = subscriber_client.get(url)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2

    # And let's pretend we change our mind and undo that. Which is basically
    # to toggle it again.
    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Foo"})}'
        ).status_code
        == 201
    )

    # Because it became an undo, it should not have moved this untoggle into
    # the first spot.
    response = subscriber_client.get(url)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 3
    assert [x["url"] for x in items] == [
        "/en-US/docs/Buzz",
        "/en-US/docs/Bar",
        # Note! Even though this was the latest to be bookmarked, it's still
        # in its original (third) place. It's because the bookmarking of it
        # was considered an "undo".
        "/en-US/docs/Foo",
    ]

    # This time, un-bookmark two but re-bookmark them in the wrong order.
    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Buzz"})}', {"delete": True}
        ).status_code
        == 200
    )
    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Bar"})}', {"delete": True}
        ).status_code
        == 200
    )

    # The last one to be touched was "Bar", let's now bookmark them back
    # but this time, do it in the opposite order.
    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Buzz"})}'
        ).status_code
        == 201
    )
    assert (
        subscriber_client.post(
            f'{url}?{urlencode({"url": "/en-US/docs/Bar"})}'
        ).status_code
        == 201
    )

    response = subscriber_client.get(url)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 3
    assert [x["url"] for x in items] == [
        # Note the the order of these two is the same. Because we only care about the creation
        # order, not the deletion time.
        "/en-US/docs/Buzz",
        "/en-US/docs/Bar",
        "/en-US/docs/Foo",
    ]
