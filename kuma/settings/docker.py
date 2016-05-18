from .common import *  # noqa

ES_LIVE_INDEX = True

LOGGING['loggers']['django.db.backends.schema'] = {
    'handlers': ['console'],
    'propagate': True,
    'level': 'WARNING',
}

SERVE_MEDIA = True
