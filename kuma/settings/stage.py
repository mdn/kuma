from .common import *  # noqa

ATTACHMENT_HOST = config('ATTACHMENT_HOST',
                         default='developer-samples.allizom.org')

EMAIL_SUBJECT_PREFIX = '[mdn stage] '

# Email
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='notifications@developer-dev.allizom.org'
)
SERVER_EMAIL = config(
    'SERVER_EMAIL',
    default='server-error@developer-dev.allizom.org'
)

DOMAIN = STAGING_DOMAIN
SITE_URL = STAGING_URL

CELERY_ALWAYS_EAGER = False
CELERYD_MAX_TASKS_PER_CHILD = 3000

ES_INDEX_PREFIX = config('ES_INDEX_PREFIX', default='mdnstage')
ES_LIVE_INDEX = config('ES_LIVE_INDEX', default=True, cast=bool)

enable_candidate_languages()
