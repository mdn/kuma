from .common import *  # noqa

ATTACHMENT_HOST = config('ATTACHMENT_HOST', default='mdn.mozillademos.org')
ALLOW_ROBOTS = True

# Email
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='no-reply@developer.mozilla.org'
)
SERVER_EMAIL = config(
    'SERVER_EMAIL',
    default='mdn-prod-noreply@mozilla.com'
)

# Cache
CACHES['memcache']['TIMEOUT'] = 60 * 60 * 24

MEDIA_URL = config('MEDIA_URL', default='https://developer.cdn.mozilla.net/media/')
DEFAULT_AVATAR = config(
    'DEFAULT_AVATAR',
    default=MEDIA_URL + 'img/avatar.png'
)

CELERY_ALWAYS_EAGER = False
CELERYD_MAX_TASKS_PER_CHILD = 500

ES_INDEX_PREFIX = config('ES_INDEX_PREFIX', default='mdnprod')
ES_LIVE_INDEX = config('ES_LIVE_INDEX', default=True, cast=bool)
