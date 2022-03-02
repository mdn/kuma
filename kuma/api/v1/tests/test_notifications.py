import json

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from model_bakery import baker

from kuma.notifications import models


def test_notifications_anonymous(client):
    response = client.get(reverse("api-v1:plus.notifications"))
    assert response.status_code == 401


def test_notifications(user_client, wiki_user):
    url = reverse("api-v1:plus.notifications")
    response = user_client.get(url)
    assert response.status_code == 200
    assert json.loads(response.content)["items"] == []

    notification = baker.make(models.Notification, user=wiki_user)

    response = user_client.get(url)
    assert response.status_code == 200
    assert json.loads(response.content)["items"] == [
        {
            "id": notification.pk,
            "created": json.loads(
                DjangoJSONEncoder().encode(notification.notification.created)
            ),
            "title": notification.notification.title,
            "text": notification.notification.text,
            "read": notification.read,
            "starred": notification.starred,
            "deleted": False
        }
    ]


def test_notifications_only_yours(user_client, wiki_user):
    notification = baker.make(models.Notification)
    assert notification.user != wiki_user

    url = reverse("api-v1:plus.notifications")
    response = user_client.get(url)
    assert response.status_code == 200
    assert json.loads(response.content)["items"] == []


def test_notifications_paginations(user_client, wiki_user):
    url = reverse("api-v1:plus.notifications")
    response = user_client.get(url)
    assert response.status_code == 200
    assert json.loads(response.content)["items"] == []

    for i in range(20):
        baker.make(models.Notification, user=wiki_user, id=i)

    response = user_client.get(url, {"limit": 10})
    assert response.status_code == 200
    items_json = json.loads(response.content)["items"]
    assert len(items_json) == 10

    for i, j in zip(range(0, 10), range(19, 10, -1)):
        # id's descending by most recent (LIFO)
        assert items_json[i]["id"] == j

    # Test offset
    response = user_client.get(url, {"limit": 10, "offset": 10})
    items_json = json.loads(response.content)["items"]

    for i, j in zip(range(0, 10), range(9, 0, -1)):
        assert items_json[i]["id"] == j


def test_notifications_paginations_deletion(user_client, wiki_user):
    url = reverse("api-v1:plus.notifications")
    for i in range(15):
        baker.make(models.Notification, user=wiki_user, id=i)

    response = user_client.get(url, {"limit": 10})
    assert response.status_code == 200
    items_json = json.loads(response.content)["items"]
    assert len(items_json) == 10

    for i, j in zip(range(0, 10), range(14, 5, -1)):
        # id's descending by most recent (LIFO)
        assert items_json[i]["id"] == j

    delete_url = reverse("api-v1:notifications_delete_id", kwargs={"pk": 5})
    # Given item 5 is deleted.
    user_client.post(delete_url)
    response = user_client.get(url, {"limit": 10})
    items_json = json.loads(response.content)["items"]

    # Last item of new fetch should now be '4'
    assert len(items_json) == 10
    assert items_json[9]["id"] == 4


def test_notifications_delete_many(user_client, wiki_user):
    url = reverse("api-v1:plus.notifications")
    for i in range(15):
        baker.make(models.Notification, user=wiki_user, id=i)

    response = user_client.get(url, {"limit": 10})
    assert response.status_code == 200
    items_json = json.loads(response.content)["items"]
    assert len(items_json) == 10

    for i, j in zip(range(0, 10), range(14, 5, -1)):
        # id's descending by most recent (LIFO)
        assert items_json[i]["id"] == j

    delete_many_url = reverse("api-v1:notifications_delete_many")
    # Given 6 items are deleted.
    response = user_client.post(
        delete_many_url,
        json.dumps({"ids": [14, 13, 12, 11, 10, 9]}),
        content_type="application/json",
    )
    assert response.status_code == 200
    # Refetch
    response = user_client.get(url, {"limit": 10})
    items_json = json.loads(response.content)["items"]
    # Ensure ids deleted as expected
    assert len(items_json) == 9
    for i, j in zip(range(0, 9), range(8, 0, -1)):
        # id's descending by most recent (LIFO)
        assert items_json[i]["id"] == j
