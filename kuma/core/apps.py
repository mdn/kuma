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
        return {lang.lower(): settings.LOCALES[lang].native
                for lang in settings.MDN_LANGUAGES}
