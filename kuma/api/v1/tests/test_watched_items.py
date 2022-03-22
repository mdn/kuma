import json

from django.urls import reverse
from model_bakery import baker

from kuma.notifications import models


def test_unwatch_manys(user_client, wiki_user):
    url = reverse("api-v1:watching")
    user_watched_items = []

    for i in range(10):
        mock_watch = baker.make(models.Watch, users=[wiki_user])
        user_watch = baker.make(
            models.UserWatch, user=wiki_user, id=i, watch=mock_watch
        )
        user_watched_items.append(user_watch)

    response = user_client.get(url, {"limit": 10})
    assert response.status_code == 200
    items_json = json.loads(response.content)["items"]
    assert len(items_json) == 10

    unwatch_many_url = reverse("api-v1:unwatch_many")

    # Given 6 items are deleted.
    del1 = user_watched_items[0].watch.url
    del2 = user_watched_items[1].watch.url
    response = user_client.post(
        unwatch_many_url,
        json.dumps(
            {
                "unwatch": [
                    del1,
                    del2,
                ]
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    # Refetch
    response = user_client.get(url, {"limit": 10})
    items_json = json.loads(response.content)["items"]
    filtered = filter(
        lambda item: item["url"] == del1 or item["url"] == del2, items_json
    )
    # Assert deleted no longer there :)
    assert len(list(filtered)) == 0
