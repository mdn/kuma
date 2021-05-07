from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FeederConfig(AppConfig):
    """
    The Django App Config class to store information about the feeder app
    and do startup time things.
    """

    name = "kuma.feeder"
    verbose_name = _("Feeder")
