from django.conf import settings

from kuma.core.utils import requests_retry_session

API_URL = "https://api.sendinblue.com/v3/"


def request(method, path, **kwargs):
    return requests_retry_session().request(
        method,
        API_URL + path,
        headers={"api-key": settings.SENDINBLUE_API_KEY, "accept": "application/json"},
        **kwargs,
    )
