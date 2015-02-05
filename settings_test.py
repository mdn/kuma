from settings import INSTALLED_APPS

INSTALLED_APPS += (
    'kuma.core.tests.taggit_extras',
    'kuma.actioncounters.tests',
)
BANISH_ENABLED = False
