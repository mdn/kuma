from .common import *  # noqa

DEBUG = True
TEMPLATE_DEBUG = True
# BROKER_URL = 'redis://redis:6379/1'
CELERY_ALWAYS_EAGER = True
ES_LIVE_INDEX = True
ES_URLS = ['elasticsearch:9200']

BANISH_ENABLED = False

LOGGING['loggers']['django.db.backends.schema'] = {
    'handlers': ['console'],
    'propagate': True,
    'level': 'WARNING',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'kuma',  # Or path to database file if using sqlite3.
        'USER': 'root',  # Not used with sqlite3.
        'PASSWORD': 'docker',  # Not used with sqlite3.
        'HOST': 'mysql',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'sql_mode': 'TRADITIONAL',
            'charset': 'utf8',
            'init_command': 'SET '
                'storage_engine=INNODB,'
                'character_set_connection=utf8,'
                'collation_connection=utf8_general_ci',
        },
        'ATOMIC_REQUESTS': True,
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'utf8_general_ci',
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': CACHE_COUNT_TIMEOUT,
        'KEY_PREFIX': CACHE_PREFIX,
    },
    'memcache': {
        'BACKEND': 'memcached_hashring.backend.MemcachedHashRingCache',
        'TIMEOUT': CACHE_COUNT_TIMEOUT * 60,
        'KEY_PREFIX': CACHE_PREFIX,
        'LOCATION': ['memcached:11211'],
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CLEANCSS_BIN = '/usr/local/bin/cleancss'
UGLIFY_BIN = '/usr/local/bin/uglifyjs'

SERVE_MEDIA = True
