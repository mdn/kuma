from django.conf import settings
from django.core.checks import Error

from kuma.core.urlresolvers import reverse
from kuma.wiki.templatetags.jinja_helpers import absolutify

from . import sendinblue

SENDINBLUE_API_ERROR = "kuma.users.sendinblue.E001"


def create_missing_attributes(existing_attributes, required_attributes):
    for name, sendinblue_type in required_attributes.items():
        if any(attribute["name"] == name for attribute in existing_attributes):
            continue

        response = sendinblue.request(
            "POST",
            f"contacts/attributes/normal/{name}",
            json={"type": sendinblue_type},
        )
        if not response.ok:
            message = response.json()["message"]
            return [
                Error(
                    f"Error when creating sendinblue attribute {name!r} of type {sendinblue_type!r}: {message}",
                    id=SENDINBLUE_API_ERROR,
                )
            ]

    return []


def create_sendinblue_attributes():
    response = sendinblue.request("GET", "contacts/attributes")
    if not response.ok:
        return [
            Error(
                f"Error getting sendinblue attributes: {response.status_code}",
                id=SENDINBLUE_API_ERROR,
            )
        ]

    return create_missing_attributes(
        response.json()["attributes"], {"USERNAME": "text", "IS_PAYING": "boolean"}
    )


# We're using sendinblue for marketing emails. Another possible use-case is "transactional"
# But as we're not using it that way, we don't have to check for that.
EMAIL_TYPE = "marketing"


def create_sendinblue_unsubscribe_webhook():
    url_path = reverse("api.v1.sendinblue_hooks")
    url = (
        "https://" + settings.CUSTOM_WEBHOOK_HOSTNAME + url_path
        if settings.CUSTOM_WEBHOOK_HOSTNAME
        else absolutify(url_path)
    )

    # From https://developers.sendinblue.com/reference#createwebhook
    # "Occurs whenever a user unsubscribes through an email's subscription management link."
    events = ("unsubscribed",)

    response = sendinblue.request("GET", "webhooks", params={"type": EMAIL_TYPE})

    no_webhooks_found = response.status_code == 404
    if not response.ok and not no_webhooks_found:
        return [
            Error(
                f"Error getting sendinblue webhooks: {response.status_code}",
                id=SENDINBLUE_API_ERROR,
            )
        ]

    if not no_webhooks_found:
        for webhook in response.json()["webhooks"]:
            if webhook["url"] == url and set(events) == set(webhook["events"]):
                return []

    response = sendinblue.request(
        "POST", "webhooks", json={"url": url, "events": events, "type": EMAIL_TYPE}
    )
    if not response.ok:
        return [
            Error(
                f"Error creating sendinblue webhook: {response.status_code}",
                id=SENDINBLUE_API_ERROR,
            )
        ]

    return []


def sendinblue_check(app_configs, **kwargs):
    if not settings.SENDINBLUE_API_KEY:
        return []

    return create_sendinblue_attributes() + create_sendinblue_unsubscribe_webhook()
