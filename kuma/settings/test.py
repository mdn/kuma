from .common import *  # noqa

ATTACHMENT_HOST = 'mdn-local.mozillademos.org'

DEBUG = False
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
ES_LIVE_INDEX = False
ES_DISABLED = True

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

INSTALLED_APPS += (
    'kuma.core.tests.taggit_extras',
    'kuma.actioncounters.tests',
)
