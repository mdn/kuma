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
            "deleted": False,
            "created": json.loads(
                DjangoJSONEncoder().encode(notification.notification.created)
            ),
            "title": notification.notification.title,
            "text": notification.notification.text,
            "url": notification.notification.page_url,
            "read": notification.read,
            "starred": notification.starred,
        }
    ]


def test_notifications_only_yours(user_client, wiki_user):
    notification = baker.make(models.Notification)
    assert notification.user != wiki_user

    url = reverse("api-v1:plus.notifications")
    response = user_client.get(url)
    assert response.status_code == 200
    assert json.loads(response.content)["items"] == []
