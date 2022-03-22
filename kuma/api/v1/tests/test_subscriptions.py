import json

import pytest
from django.urls import reverse

from kuma.users import models


@pytest.mark.django_db
def test_subscriptions(subscriber_client, wiki_user):
    response = subscriber_client.get(reverse("api-v1:whoami"))
    assert response.status_code == 200
    assert json.loads(response.content) == {
        "username": wiki_user.username,
        "is_authenticated": True,
        "email": wiki_user.email,
        "is_subscriber": True,
        "subscription_type": "",
        "avatar_url": "",
    }

    # Add Subscription and save model back to db
    profile = models.UserProfile.objects.get(user=wiki_user)
    profile.subscription_type = models.UserProfile.SubscriptionType.MDN_PLUS_10Y
    profile.is_subscriber = True
    profile.save()

    # Assert subscription type present in response
    response = subscriber_client.get(reverse("api-v1:whoami"))
    assert response.status_code == 200
    assert json.loads(response.content) == {
        "username": wiki_user.username,
        "is_authenticated": True,
        "email": wiki_user.email,
        "is_subscriber": True,
        "subscription_type": models.UserProfile.SubscriptionType.MDN_PLUS_10Y.value,
        "avatar_url": "",
    }
