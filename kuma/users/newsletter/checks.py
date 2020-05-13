from django.conf import settings
from django.core.checks import Error

from . import sendinblue

SENDINBLUE_ERROR = "kuma.users.sendinblue.E001"


def sendinblue_check(app_configs, **kwargs):
    if not settings.SENDINBLUE_API_KEY:
        return []

    response = sendinblue.request("GET", "contacts/attributes")
    if not response.ok:
        return [
            Error(
                f"Error when creating sendinblue attribute: {response.json()['message']}",
                id=SENDINBLUE_ERROR,
            )
        ]

    if not any(
        attribute["name"] == "IS_PAYING" for attribute in response.json()["attributes"]
    ):
        response = sendinblue.request(
            "POST", "contacts/attributes/normal/IS_PAYING", json={"type": "boolean"},
        )
        if not response.ok:
            return [
                Error(
                    f"Error when creating sendinblue attribute: {response.json()['message']}",
                    id=SENDINBLUE_ERROR,
                )
            ]

    return []
