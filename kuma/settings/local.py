import logging
from .common import *  # noqa

ATTACHMENT_HOST = 'mdn-local.mozillademos.org'

INTERNAL_IPS = ('127.0.0.1', '192.168.10.1')

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SERVE_MEDIA = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

DEMO_UPLOADS_ROOT = path('uploads', 'demos')
DEMO_UPLOADS_URL = '/media/uploads/demos/'

CELERY_ALWAYS_EAGER = True

INSTALLED_APPS += (
    'django_extensions',
    'devserver',
)

if config('DEBUG_TOOLBAR', default=False, cast=bool):
    INSTALLED_APPS += (
        'debug_toolbar',
    )

    JINGO_EXCLUDE_APPS += (
        'debug_toolbar',
    )

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
)

DEVSERVER_MODULES = (
    # sql modules interfere with saving some KumaScript templates
    # 'devserver.modules.sql.SQLRealTimeModule',
    # 'devserver.modules.sql.SQLSummaryModule',
    'devserver.modules.profile.ProfileSummaryModule',
    'devserver.modules.profile.MemoryUseModule',
    'devserver.modules.cache.CacheSummaryModule',

    # Modules not enabled by default
    # 'devserver.modules.ajax.AjaxDumpModule',
    # 'devserver.modules.profile.LineProfilerModule',
)

LOG_LEVEL = logging.ERROR

PROTOCOL = 'https://'
DOMAIN = 'developer-local.allizom.org'
SITE_URL = PROTOCOL + DOMAIN

SOCIALACCOUNT_PROVIDERS['persona']['AUDIENCE'] = SITE_URL

# Elasticsearch related settings.
ES_DEFAULT_NUM_REPLICAS = 0
ES_DEFAULT_NUM_SHARDS = 1
