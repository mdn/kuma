import copy
from urllib.parse import urlencode

import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.django_db
def test_bookmarked_anonymous(client):
    response = client.get(
        reverse("api.v1.plus.bookmarks.bookmarked"),
    )
    assert response.status_code == 403
    assert "not signed in" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_is_bookmarked_signed_in(user_client, wiki_user, settings):
    url = reverse("api.v1.plus.bookmarks.bookmarked")
    response = user_client.get(url)
    print(response.content)
    assert response.status_code == 403
    assert "not a subscriber" in response.content.decode("utf-8")

    # TEMPORARY until all things auth + subscription come together.
    settings.FAKE_USER_SUBSCRIBER_NUMBER = 1234
    response = user_client.get(url)
    assert response.status_code == 400
    assert "missing 'url'" in response.content.decode("utf-8")

    response = user_client.get(url, {"url": "some junk"})
    assert response.status_code == 400
    assert "invalid 'url'" in response.content.decode("utf-8")

    response = user_client.get(url, {"url": "/not/a/mdny/url"})
    assert response.status_code == 400
    assert "invalid 'url'" in response.content.decode("utf-8")

    response = user_client.get(url, {"url": "/docs/://ftphack"})
    assert response.status_code == 400
    assert "invalid 'url'" in response.content.decode("utf-8")

    response = user_client.get(url, {"url": "/en-US/docs/Web"})
    assert response.status_code == 200
    # It's NOT been toggled yet
    assert response.json()["bookmarked"] is None
    assert response.json()["csrfmiddlewaretoken"]


@pytest.mark.django_db
def test_toggle_bookmarked(user_client, wiki_user, mock_requests, settings):
    # TEMPORARY until all things auth + subscription come together.
    settings.FAKE_USER_SUBSCRIBER_NUMBER = 1234

    doc_data = {
        "doc": {
            "title": "Web",
        }
    }

    mock_requests.register_uri(
        "GET", settings.BOOKMARKS_BASE_URL + "/en-US/docs/Web/index.json", json=doc_data
    )

    url = reverse("api.v1.plus.bookmarks.bookmarked")
    get_url = f'{url}?{urlencode({"url": "/en-US/docs/Web"})}'
    response = user_client.post(get_url)
    assert response.status_code == 201

    response = user_client.get(get_url)
    assert response.status_code == 200
    assert response.json()["bookmarked"]["id"]
    initial_id = response.json()["bookmarked"]["id"]
    assert response.json()["bookmarked"]["created"]
    assert response.json()["csrfmiddlewaretoken"]

    # Now toggle it off
    response = user_client.post(get_url)
    assert response.status_code == 201

    # Soft deleted
    response = user_client.get(get_url)
    assert response.status_code == 200
    assert not response.json()["bookmarked"]

    # And undo the soft-delete
    response = user_client.post(get_url)
    assert response.status_code == 201

    # Should return with the same ID as before
    response = user_client.get(get_url)
    assert response.status_code == 200
    response = user_client.get(get_url)
    assert response.status_code == 200
    assert response.json()["bookmarked"]["id"] == initial_id

    # Case sensitive too
    response = user_client.get(get_url.replace("en-US", "EN-us"))
    assert response.status_code == 200
    assert response.json()["bookmarked"]


@pytest.mark.django_db
def test_bookmarks_anonymous(client):
    response = client.get(
        reverse("api.v1.plus.bookmarks.all"),
    )
    assert response.status_code == 403
    assert "not signed in" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_bookmarks_signed_in(user_client, wiki_user, settings):
    url = reverse("api.v1.plus.bookmarks.all")
    response = user_client.get(url)
    assert response.status_code == 403
    assert "not a subscriber" in response.content.decode("utf-8")

    # TEMPORARY until all things auth + subscription come together.
    settings.FAKE_USER_SUBSCRIBER_NUMBER = 1234
    response = user_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0
    assert response.json()["metadata"]["total"] == 0
    assert response.json()["metadata"]["page"] == 1
    assert response.json()["metadata"]["per_page"] > 0

    # Try to mess with the `page` and `per_page`
    response = user_client.get(url, {"page": "xxx"})
    assert response.status_code == 400
    assert "invalid 'page'" in response.content.decode("utf-8")
    response = user_client.get(url, {"page": "-1"})
    assert response.status_code == 400
    assert "invalid 'page'" in response.content.decode("utf-8")
    response = user_client.get(url, {"page": "999"})
    assert response.status_code == 400
    assert "invalid 'page'" in response.content.decode("utf-8")
    response = user_client.get(url, {"per_page": "999"})
    assert response.status_code == 400
    assert "invalid 'per_page'" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_bookmarks_pagination(user_client, wiki_user, mock_requests, settings):
    # TEMPORARY until all things auth + subscription come together.
    settings.FAKE_USER_SUBSCRIBER_NUMBER = 1234

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

    url = reverse("api.v1.plus.bookmarks.bookmarked")

    for i in range(1, 21):
        mdn_url = f"/en-US/docs/Web/Doc{i}"
        doc_absolute_url = settings.BOOKMARKS_BASE_URL + mdn_url + "/index.json"
        mock_requests.register_uri(
            "GET", doc_absolute_url, json=create_doc_data(mdn_url, f"Doc {i}")
        )
        get_url = f'{url}?{urlencode({"url": mdn_url})}'
        response = user_client.post(get_url)
        assert response.status_code == 201

    # Add one extra but this one toggle twice so it becomes soft-deleted
    i += 1
    mdn_url = f"/en-US/docs/Web/Doc{i}"
    doc_absolute_url = settings.BOOKMARKS_BASE_URL + mdn_url + "/index.json"
    mock_requests.register_uri(
        "GET", doc_absolute_url, json=create_doc_data(mdn_url, f"Doc {i}")
    )
    get_url = f'{url}?{urlencode({"url": mdn_url})}'
    response = user_client.post(get_url)
    assert response.status_code == 201
    response = user_client.post(get_url)
    assert response.status_code == 201

    url = reverse("api.v1.plus.bookmarks.all")
    response = user_client.get(url, {"per_page": "5"})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 5
    assert response.json()["metadata"]["total"] == 20
    assert response.json()["metadata"]["page"] == 1
    assert response.json()["metadata"]["per_page"] == 5

    response = user_client.get(url, {"per_page": "5", "page": "2"})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 5
    assert response.json()["metadata"]["total"] == 20
    assert response.json()["metadata"]["page"] == 2
    assert response.json()["metadata"]["per_page"] == 5


def test_undo_bookmark(user_client, wiki_user, mock_requests, settings):
    # TEMPORARY until all things auth + subscription come together.
    settings.FAKE_USER_SUBSCRIBER_NUMBER = 1234

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

    bookmark_url = reverse("api.v1.plus.bookmarks.bookmarked")

    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Foo"})}'
        ).status_code
        == 201
    )

    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Bar"})}'
        ).status_code
        == 201
    )

    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Buzz"})}'
        ).status_code
        == 201
    )

    bookmarks_url = reverse("api.v1.plus.bookmarks.all")
    response = user_client.get(bookmarks_url)
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
    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Foo"})}'
        ).status_code
        == 201
    )

    # Check that it disappears from the listing
    response = user_client.get(bookmarks_url)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2

    # And let's pretend we change our mind and undo that. Which is basically
    # to toggle it again.
    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Foo"})}'
        ).status_code
        == 201
    )

    # Because it became an undo, it should not have moved this untoggle into
    # the first spot.
    response = user_client.get(bookmarks_url)
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
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Buzz"})}'
        ).status_code
        == 201
    )
    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Bar"})}'
        ).status_code
        == 201
    )

    # The last one to be touched was "Bar", let's now bookmark them back
    # but this time, do it in the opposite order.
    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Buzz"})}'
        ).status_code
        == 201
    )
    assert (
        user_client.post(
            f'{bookmark_url}?{urlencode({"url": "/en-US/docs/Bar"})}'
        ).status_code
        == 201
    )

    response = user_client.get(bookmarks_url)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 3
    assert [x["url"] for x in items] == [
        # Note the these two have changed order! The most recently bookmarked
        # on top. Because it wasn't an act over undo.
        "/en-US/docs/Bar",
        "/en-US/docs/Buzz",
        "/en-US/docs/Foo",
    ]
