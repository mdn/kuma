from urllib.parse import quote

from celery import task
from django.conf import settings

from kuma.users.models import User, UserSubscription

from . import sendinblue


@task
def create_or_update_contact(user_pk):
    user = User.objects.get(pk=user_pk)

    if not user.is_newsletter_subscribed:
        return

    response = sendinblue.request(
        "POST",
        "contacts",
        json={
            "updateEnabled": True,
            "email": user.email,
            "attributes": {
                "USERNAME": user.username,
                "IS_PAYING": UserSubscription.objects.filter(
                    user=user, canceled__isnull=True
                ).exists(),
            },
            "listIds": [int(settings.SENDINBLUE_LIST_ID)],
        },
    )
    response.raise_for_status()


@task
def delete_contact(email):
    response = sendinblue.request("DELETE", f"contacts/{quote(email)}")
    response.raise_for_status()
