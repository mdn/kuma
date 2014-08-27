from django.conf import settings
from django.core.management import call_command
from django.db.models import loading

from notifications.models import Watch, WatchFilter
from sumo.tests import TestCase
from kuma.users.tests import user


def watch(save=False, **kwargs):
    # TODO: better defaults, when there are events available.
    defaults = {'user': kwargs.get('user') or user(),
                'is_active': True}
    defaults.update(kwargs)
    w = Watch.objects.create(**defaults)
    if save:
        w.save()
    return w


def watch_filter(save=False, **kwargs):
    defaults = {'watch': kwargs.get('watch') or watch(),
                'name': 'test',
                'value': 1234}
    defaults.update(kwargs)
    f = WatchFilter.objects.create(**defaults)
    if save:
        f.save()
    return f


class ModelsTestCase(TestCase):
    """Does some pre-setup and post-teardown work to create tables for any
    of your test models.

    Simply subclass this and set self.apps to a tuple of *additional*
    installed apps. These will be added *after* the ones in
    settings.INSTALLED_APPS.

    Based on http://stackoverflow.com/questions/502916#1827272

    """
    apps = []

    def _pre_setup(self):
        # Add the models to the db.
        self._original_installed_apps = list(settings.INSTALLED_APPS)
        for app in self.apps:
            settings.INSTALLED_APPS.append(app)
        loading.cache.loaded = False
        call_command('syncdb', interactive=False, verbosity=0)
        # Call the original method that does the fixtures etc.
        super(ModelsTestCase, self)._pre_setup()

    def _post_teardown(self):
        # Call the original method.
        super(ModelsTestCase, self)._post_teardown()
        # Restore the settings.
        settings.INSTALLED_APPS = self._original_installed_apps
        loading.cache.loaded = False
