from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SearchConfig(AppConfig):
    """Initialize the kuma.search application."""

    name = "kuma.search"
    verbose_name = _("Search")
