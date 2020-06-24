from urllib.parse import quote

from django.conf import settings

from kuma.users.models import User

from . import sendinblue


def check_is_in_sendinblue_list(email):
    response = sendinblue.request("GET", f"contacts/email/{quote(email)}")
    if response.ok:
        return settings.SENDINBLUE_LIST_ID in response.json()["listIds"]
    elif response.status_code == 404:
        return False
    else:
        response.raise_for_status()


def refresh_is_user_newsletter_subscribed(email):
    User.objects.filter(email=email).update(
        is_newsletter_subscribed=check_is_in_sendinblue_list(email)
    )
