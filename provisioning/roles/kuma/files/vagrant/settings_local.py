from settings import *
import logging

INTERNAL_IPS = ('127.0.0.1', '192.168.10.1',)

# ALLOWED_HOSTS must be set whenever DEBUG = False
ALLOWED_HOSTS = '*'

DEBUG = True
DEV = True
TEMPLATES[1]['OPTIONS']['debug'] = DEBUG
SERVE_MEDIA = DEBUG

SESSION_COOKIE_SECURE = True

DEMO_UPLOADS_ROOT = '/home/vagrant/uploads/demos'
DEMO_UPLOADS_URL = '/media/uploads/demos/'

PROD_DETAILS_DIR = '/home/vagrant/product_details_json'

GOOGLE_MAPS_API_KEY = "ABQIAAAANRj9BHQi5ireVluCwVy0yRSrufPN8BjQWjkoRva24PCQEXS2OhSXu2BEgUH5PmGOmW71r2-tEuOVuQ"

BITLY_USERNAME = 'lmorchard'
BITLY_API_KEY = "R_2653e6351e31d02988b3da31dac6e2c0"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
#EMAIL_FILE_PATH = '/home/vagrant/logs/kuma-email.log'

# Uncomment to enable a real celery queue
CELERY_ALWAYS_EAGER = False

# This is used to hash some things in Django.
SECRET_KEY = 'jenny8675309'

DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

LOG_LEVEL = logging.DEBUG

SITE_URL = 'https://developer-local.allizom.org'
PROTOCOL = 'https://'
DOMAIN = 'developer-local.allizom.org'

KUMASCRIPT_URL_TEMPLATE = 'http://localhost:9080/docs/{path}'

ATTACHMENT_HOST = 'mdn-local.mozillademos.org'

# Elasticsearch related settings.
ES_DEFAULT_NUM_REPLICAS = 0
ES_DEFAULT_NUM_SHARDS = 5
ES_DEFAULT_REFRESH_INTERVAL = '5s'
ES_DISABLED = False
ES_INDEX_PREFIX = 'mdn'
ES_INDEXES = {'default': 'main_index'}
# Specify the extra timeout in seconds for the indexing ES connection.
ES_INDEXING_TIMEOUT = 30
ES_LIVE_INDEX = True
ES_URLS = ['localhost:9200']


# See https://mana.mozilla.org/wiki/display/websites/Developer+Cluster#DeveloperCluster-Sentry
SENTRY_DSN = ''

if SENTRY_DSN:
    INSTALLED_APPS = INSTALLED_APPS + (
        'raven.contrib.django.raven_compat',
    )

SOCIALACCOUNT_PROVIDERS['persona']['AUDIENCE'] = 'https://developer-local.allizom.org'

# Don't cache non-versioned static files in DEBUG mode
if DEBUG:
    WHITENOISE_MAX_AGE = 0
