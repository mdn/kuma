from django.apps import AppConfig
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _


class CoreConfig(AppConfig):
    """
    The Django App Config class to store information about the core app
    and do startup time things.
    """
    name = 'kuma.core'
    verbose_name = _('Core')

    @cached_property
    def language_mapping(self):
        """
        a static mapping of lower case language names and their native names
        """
        # LANGUAGES settings return a list of tuple with language code and their native name
        # Make the language code lower and convert the tuple to dictionary
        return {lang[0].lower(): lang[1] for lang in settings.LANGUAGES}
