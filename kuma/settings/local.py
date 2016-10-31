import logging
from .common import *  # noqa

# Settings for Vagrant Development
# TODO: Use environment to override, not settings picker

DEFAULT_FILE_STORAGE = 'kuma.core.storage.KumaHttpStorage'
LOCALDEVSTORAGE_HTTP_FALLBACK_DOMAIN = PRODUCTION_URL + '/media/'

ATTACHMENT_HOST = 'mdn-local.mozillademos.org'

INTERNAL_IPS = ('127.0.0.1', '192.168.10.1')

# Default DEBUG to True, and recompute derived settings
DEBUG = config('DEBUG', default=True, cast=bool)
DEBUG_TOOLBAR = config('DEBUG_TOOLBAR', default=False, cast=bool)
SERVE_MEDIA = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
PIPELINE['PIPELINE_ENABLED'] = config('PIPELINE_ENABLED', not DEBUG, cast=bool)
PIPELINE['PIPELINE_COLLECTOR_ENABLED'] = config('PIPELINE_COLLECTOR_ENABLED',
                                                not DEBUG, cast=bool)
TEMPLATES[1]['OPTIONS']['debug'] = DEBUG

LOG_LEVEL = logging.ERROR
PROTOCOL = config('PROTOCOL', default='https://')
DOMAIN = config('DOMAIN', default='developer-local.allizom.org')
SITE_URL = config('SITE_URL', default=PROTOCOL + DOMAIN)
SOCIALACCOUNT_PROVIDERS['persona']['AUDIENCE'] = SITE_URL

# Elasticsearch related settings.
ES_DEFAULT_NUM_REPLICAS = 0
ES_DEFAULT_NUM_SHARDS = 1
ES_LIVE_INDEX = True

# Don't cache non-versioned static files in DEBUG mode
if DEBUG:
    WHITENOISE_MAX_AGE = 0
    if DEBUG_TOOLBAR:
        INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)
