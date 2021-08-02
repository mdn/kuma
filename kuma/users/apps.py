from django.core.checks import register
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "kuma.users"
    verbose_name = _("Users")

    def ready(self):
        self.register_checks()

    def register_checks(self):
        from .checks import oidc_config_check

        register(oidc_config_check)
