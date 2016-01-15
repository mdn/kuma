from settings import *

DEBUG = False
TEMPLATE_DEBUG = True
CELERY_ALWAYS_EAGER = True
ES_LIVE_INDEX = False
ES_URLS = ['localhost:9200']

INSTALLED_APPS += (
    'kuma.core.tests.taggit_extras',
    # testing.
    'django_nose',
)
BANISH_ENABLED = False

LOGGING['loggers'].update({
    'django.db.backends': {
        'handlers': ['console'],
        'propagate': True,
        'level': 'WARNING',
    },
    'kuma.search.utils': {
        'handlers': [],
        'propagate': False,
        'level': 'CRITICAL',
    },
})

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--traverse-namespace',  # make sure `./manage.py test kuma` works
]
