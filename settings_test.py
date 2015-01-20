from settings import INSTALLED_APPS

CELERY_ALWAYS_EAGER = True
ES_LIVE_INDEX = False

INSTALLED_APPS += ('kuma.core.tests.taggit_extras',)
