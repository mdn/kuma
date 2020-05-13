from urllib.parse import quote

from celery import task

from . import api


@task
def sendinblue_create_or_update_contact(email, attributes=None):
    response = api.request(
        "POST",
        "contacts",
        json={
            "updateEnabled": True,
            "email": email,
            "attributes": attributes or {},
            "listIds": [int(api.LIST_ID)],
        },
    )
    response.raise_for_status()


@task
def sendinblue_delete_contact(email):
    response = api.request("DELETE", f"contacts/{quote(email)}")
    response.raise_for_status()
