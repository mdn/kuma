import stripe
from django.conf import settings
from django.contrib.auth.apps import AuthConfig
from django.utils.translation import ugettext_lazy as _


class UserConfig(AuthConfig):
    """
    The Django App Config class to store information about the users app
    and do startup time things.
    """

    name = "kuma.users"
    verbose_name = _("User")

    def ready(self):
        # Connect signal handlers
        from . import signal_handlers  # noqa

        # Configure global 'stripe' module
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.max_network_retries = settings.STRIPE_MAX_NETWORK_RETRIES
