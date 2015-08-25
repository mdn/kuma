from settings import *

DEBUG = False
CELERY_ALWAYS_EAGER = True
ES_LIVE_INDEX = False
ES_URLS = ['localhost:9200']

INSTALLED_APPS += (
    'kuma.core.tests.taggit_extras',
    'kuma.actioncounters.tests',
)
BANISH_ENABLED = False

DEMO_UPLOADS_ROOT = '/home/vagrant/uploads/demos'

LOGGING['loggers']['django.db.backends.schema'] = {
    'handlers': ['console'],
    'propagate': True,
    'level': 'WARNING',
}
