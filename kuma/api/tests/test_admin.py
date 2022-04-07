import json

from django.conf import settings
from django.urls import reverse
from model_bakery import baker

from kuma.notifications import models


def test_admin_update_content(user_client, wiki_user):
    # Prepare: Watch page.
    page_title = "<dialog>: The Dialog element"
    page_url = "/en-us/docs/web/html/element/dialog"
    baker.make(models.Watch, users=[wiki_user], title=page_title, url=page_url)

    # Test: Trigger content update.
    url = reverse("admin_api:admin.update_content")
    auth_headers = {
        "HTTP_AUTHORIZATION": f"Bearer {settings.NOTIFICATIONS_ADMIN_TOKEN}",
    }
    response = user_client.post(
        url,
        json.dumps(
            {
                "page": "/en-US/docs/Web/HTML/Element/dialog",
                "pr": "https://github.com/mdn/content/pull/14607",
            }
        ),
        content_type="application/json",
        **auth_headers,
    )

    assert response.status_code == 200

    # Verify: Notification was created.
    url = reverse("api-v1:plus.notifications")
    response = user_client.get(url)
    assert response.status_code == 200

    notifications = json.loads(response.content)["items"]
    assert len(notifications) == 1

    notification = notifications[0]
    assert notification["title"] == page_title
    assert notification["url"] == page_url
    assert notification["text"] == "Page updated (see PR!mdn/content!14607!!)"
