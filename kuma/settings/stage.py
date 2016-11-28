from .common import *  # noqa

ATTACHMENT_HOST = 'developer-samples.allizom.org'

EMAIL_SUBJECT_PREFIX = '[mdn stage] '

# Email
DEFAULT_FROM_EMAIL = 'no-reply@developer.allizom.org'
SERVER_EMAIL = 'mdn-stage-noreply@mozilla.com'

DOMAIN = STAGING_DOMAIN
SITE_URL = STAGING_URL

CELERY_ALWAYS_EAGER = False
CELERYD_MAX_TASKS_PER_CHILD = 3000

ES_INDEX_PREFIX = 'mdnstage'
ES_LIVE_INDEX = True
