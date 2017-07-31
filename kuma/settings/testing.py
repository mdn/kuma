from .local import *  # noqa

DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = True  # Enable recording of templates
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
ES_LIVE_INDEX = False

# SHA1 because it is fast, and hard-coded in the test fixture JSON.
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

INSTALLED_APPS += (
    'kuma.core.tests.taggit_extras',
)

LOGGING['loggers'].update({
    'django.db.backends': {
        'handlers': ['console'],
        'propagate': True,
        'level': 'WARNING',
    },
    'kuma.search.utils': {
        'handlers': [],
        'propagate': False,
        'level': 'CRITICAL',
    },
})

# Use un-versioned file names, like main.css, instead of versioned
# filenames requiring hashing, like mdn.1cb62215bf0c.css
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

# Switch Pipeline to DEBUG=False / Production values

# The documents claim True means assets should be compressed, which seems like
# more work, but it is 4x slower when False, maybe because it detects the
# existence of the file and skips generating a new one.
PIPELINE['PIPELINE_ENABLED'] = True

# The documents suggest this does nothing when PIPELINE_ENABLED=True. But,
# testing shows that tests run faster when set to True.
PIPELINE['PIPELINE_COLLECTOR_ENABLED'] = True

# We need the real Sass compiler here instead of the pass-through used for
# local dev.
PIPELINE['COMPILERS'] = ('kuma.core.pipeline.sass.SassThenPostCssCompiler',)

# Testing with django-pipeline 1.6.8, PipelineStorage
# Enabled=T, Collector=T -   482s
# Enabled=T, Collector=F -   535s
# Enabled=F, Collector=T - 18262s
# Enabled=F, Collector=F -  2043s
