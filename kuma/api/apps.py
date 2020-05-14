from django.apps import AppConfig


class APIConfig(AppConfig):
    """
    The Django App Config class to store information about the API app
    and do startup time things.
    """

    name = "kuma.api"
    verbose_name = "API"
