from urllib.parse import quote

from celery import task

from . import sendinblue


@task
def create_or_update_contact(email, attributes=None):
    response = sendinblue.request(
        "POST",
        "contacts",
        json={
            "updateEnabled": True,
            "email": email,
            "attributes": attributes or {},
            "listIds": [int(sendinblue.LIST_ID)],
        },
    )
    response.raise_for_status()


@task
def delete_contact(email):
    response = sendinblue.request("DELETE", f"contacts/{quote(email)}")
    response.raise_for_status()
