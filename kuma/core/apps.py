from django.apps import AppConfig
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from kuma.celery import app


class CoreConfig(AppConfig):
    """
    The Django App Config class to store information about the core app
    and do startup time things.
    """

    name = "kuma.core"
    verbose_name = _("Core")

    def ready(self):
        """Configure kuma.core after models are loaded."""
        # Clean up expired sessions every 60 minutes
        from kuma.core.tasks import clean_sessions

        app.add_periodic_task(60 * 60, clean_sessions.s())

    @cached_property
    def language_mapping(self):
        """
        a static mapping of lower case language names and their native names
        """
        # LANGUAGES settings return a list of tuple with language code and their native name
        # Make the language code lower and convert the tuple to dictionary
        return {lang[0].lower(): lang[1] for lang in settings.LANGUAGES}
