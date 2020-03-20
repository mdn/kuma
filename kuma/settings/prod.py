from .common import *

ATTACHMENT_HOST = config("ATTACHMENT_HOST", default="mdn.mozillademos.org")
ALLOW_ROBOTS = config("ALLOW_ROBOTS", default=True, cast=bool)

# Email
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL", default="no-reply@developer.mozilla.org"
)
SERVER_EMAIL = config("SERVER_EMAIL", default="mdn-prod-noreply@mozilla.com")

# Cache
CACHES["default"]["TIMEOUT"] = 60 * 60 * 24

MEDIA_URL = config("MEDIA_URL", default="https://developer.cdn.mozilla.net/media/")

CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", False, cast=bool)
CELERYD_MAX_TASKS_PER_CHILD = (
    config("CELERYD_MAX_TASKS_PER_CHILD", default=500, cast=int) or None
)

ES_INDEX_PREFIX = config("ES_INDEX_PREFIX", default="mdnprod")
ES_LIVE_INDEX = config("ES_LIVE_INDEX", default=True, cast=bool)
