from settings import *
import logging

INTERNAL_IPS = ('127.0.0.1', '192.168.10.1',)

DEBUG = True
DEV = True
TEMPLATE_DEBUG = DEBUG
SERVE_MEDIA = DEBUG

SESSION_COOKIE_SECURE = True

DEMO_UPLOADS_ROOT = '/home/vagrant/uploads/demos'
DEMO_UPLOADS_URL = '/media/uploads/demos/'

PROD_DETAILS_DIR = '/home/vagrant/product_details_json'
MDC_PAGES_DIR    = '/home/vagrant/mdc_pages'

GOOGLE_MAPS_API_KEY = "ABQIAAAANRj9BHQi5ireVluCwVy0yRSrufPN8BjQWjkoRva24PCQEXS2OhSXu2BEgUH5PmGOmW71r2-tEuOVuQ"

RECAPTCHA_USE_SSL = True
RECAPTCHA_PUBLIC_KEY = '6LdX8cISAAAAAA9HRXmzrcRSFsUoIK9u0nWpvGS_'
RECAPTCHA_PRIVATE_KEY = '6LdX8cISAAAAACkC1kqYmpeSf-1geTmLzrLnq0t6'

BITLY_USERNAME = 'lmorchard'
BITLY_API_KEY = "R_2653e6351e31d02988b3da31dac6e2c0"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
#EMAIL_FILE_PATH = '/home/vagrant/logs/kuma-email.log'

# Uncomment to enable a real celery queue
#CELERY_ALWAYS_EAGER = False

INSTALLED_APPS = INSTALLED_APPS + (
    "django_extensions",
    # TODO: re-enable after django 1.4
    # "debug_toolbar",
    "devserver",
)

MIDDLEWARE_CLASSES = (
    # TODO: re-enable after django 1.4
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
) + MIDDLEWARE_CLASSES

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
}

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    #'cache_panel.CachePanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

DEVSERVER_MODULES = (
    # sql modules interfere with saving some KumaScript templates
    #'devserver.modules.sql.SQLRealTimeModule',
    #'devserver.modules.sql.SQLSummaryModule',
    'devserver.modules.profile.ProfileSummaryModule',

    # Modules not enabled by default
    #'devserver.modules.ajax.AjaxDumpModule',
    #'devserver.modules.profile.MemoryUseModule',
    #'devserver.modules.cache.CacheSummaryModule',
    #'devserver.modules.profile.LineProfilerModule',
)

# The default database should point to the master.
DATABASES = {
    'default': {
        'NAME': 'kuma',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'kuma',
        'PASSWORD': 'kuma',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    },
}

MIGRATION_DATABASES = {
    'wikidb': {
        'NAME': 'wikidb',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'wikiuser',
        'PASSWORD': '2yeOr7ByBUMBiB4z',
    },
}

CACHES = {
    'default': {
        # HACK: We currently have 'default' memcache disabled in production.
        # This reflects that in local dev.
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        #'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        #'LOCATION': [
        #    '127.0.0.1:11211',
        #],
        'TIMEOUT': 3600,
        'KEY_PREFIX': 'kuma',
    },
    'secondary': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            '127.0.0.1:11211',
        ],
        'TIMEOUT': 3600,
        'KEY_PREFIX': 'kuma',
    }
}

# TODO: Switch this to 'default' when main cache issues are resolved
SECONDARY_CACHE_ALIAS = 'secondary'

# Use IP:PORT pairs separated by semicolons.
CACHE_BACKEND = 'memcached://localhost:11211?timeout=60'
CONSTANCE_DATABASE_CACHE_BACKEND = CACHE_BACKEND

# This is used to hash some things in Django.
SECRET_KEY = 'jenny8675309'

DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

LOG_LEVEL = logging.DEBUG
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(message)s',
    # filename = '/home/vagrant/logs/kuma-django.log',
)

SPHINX_INDEXER = '/usr/local/bin/indexer'
SPHINX_SEARCHD = '/usr/local/bin/searchd'
SEARCH_CACHE_PERIOD = 0 

SITE_URL = 'https://developer-local.allizom.org'
PROTOCOL = 'https://'
DOMAIN = 'developer-local.allizom.org'

# See: https://github.com/mozilla/django-browserid/issues/8 (TODO)
BROWSERID_DISABLE_CERT_CHECK = True
BROWSERID_CACERT_FILE = None

LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL_FAILURE = '/'

KUMASCRIPT_URL_TEMPLATE = 'http://localhost:9080/docs/{path}'

ATTACHMENT_HOST = 'mdn-local.mozillademos.org'

ES_DISABLED = False
ES_URLS = ['http://127.0.0.1:9200']
ES_INDEXES = {'default': 'main_index'}
ES_INDEX_PREFIX = 'mdn'
ES_LIVE_INDEX = True
ES_INDEXING_TIMEOUT = 30

SENTRY_DSN = 'https://mana.mozilla.org/wiki/display/websites/Developer+Cluster#DeveloperCluster-Sentry'
