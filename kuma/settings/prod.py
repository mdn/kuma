from .common import *  # noqa

ATTACHMENT_HOST = 'mdn.mozillademos.org'

# Email
DEFAULT_FROM_EMAIL = 'no-reply@developer.mozilla.org'
SERVER_EMAIL = 'mdn-prod-noreply@mozilla.com'

# Cache
CACHES['memcache'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': config('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'memcache'

MEDIA_URL = 'https://developer.cdn.mozilla.net/media/'
DEFAULT_AVATAR = MEDIA_URL + 'img/avatar.png'
DEMO_UPLOADS_URL = MEDIA_URL + 'uploads/demos/'

CELERY_ALWAYS_EAGER = False
CELERYD_MAX_TASKS_PER_CHILD = 500

ES_INDEX_PREFIX = 'mdnprod'
ES_LIVE_INDEX = True
