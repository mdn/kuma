from .local import *  # noqa

DEBUG = False
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
ES_LIVE_INDEX = False

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

INSTALLED_APPS += (
    'kuma.core.tests.taggit_extras',
)

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
