from .common import *  # noqa

ATTACHMENT_HOST = 'mdn.mozillademos.org'

# Email
DEFAULT_FROM_EMAIL = 'no-reply@developer.mozilla.org'
SERVER_EMAIL = 'mdn-prod-noreply@mozilla.com'

# Cache
CACHES['memcache']['TIMEOUT'] = 60 * 60 * 24

MEDIA_URL = 'https://developer.cdn.mozilla.net/media/'
DEFAULT_AVATAR = MEDIA_URL + 'img/avatar.png'

CELERY_ALWAYS_EAGER = False
CELERYD_MAX_TASKS_PER_CHILD = 500

ES_INDEX_PREFIX = 'mdnprod'
ES_LIVE_INDEX = True
