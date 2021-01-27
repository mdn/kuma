from .local import *

DEBUG = False
ENABLE_RESTRICTIONS_BY_HOST = False
TEMPLATES[0]["OPTIONS"]["debug"] = True  # Enable recording of templates
CELERY_TASK_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
ES_LIVE_INDEX = config("ES_LIVE_INDEX", default=False, cast=bool)

# Always make sure we never test against a real Elasticsearch server
ES_URLS = ["1.2.3.4:9200"]
# This makes sure that if we ever fail to mock the connection,
# it won't retry for many many seconds.
ES_RETRY_SLEEPTIME = 0
ES_RETRY_ATTEMPTS = 1
ES_RETRY_JITTER = 0

# Disable the Constance database cache
CONSTANCE_DATABASE_CACHE_BACKEND = False

# SHA1 because it is fast, and hard-coded in the test fixture JSON.
PASSWORD_HASHERS = ("django.contrib.auth.hashers.SHA1PasswordHasher",)

INSTALLED_APPS += ("kuma.core.tests.taggit_extras",)

LOGGING["loggers"].update(
    {
        "django.db.backends": {
            "handlers": ["console"],
            "propagate": True,
            "level": "WARNING",
        },
        "kuma.search.utils": {"handlers": [], "propagate": False, "level": "CRITICAL"},
    }
)


# Change the cache key prefix for tests, to avoid overwriting runtime.
for cache_settings in CACHES.values():
    current_prefix = cache_settings.get("KEY_PREFIX", "")
    cache_settings["KEY_PREFIX"] = "test." + current_prefix

# Use un-versioned file names, like main.css, instead of versioned
# filenames requiring hashing, like mdn.1cb62215bf0c.css
STATICFILES_STORAGE = "pipeline.storage.PipelineStorage"

# Switch Pipeline to DEBUG=False / Production values

# The documents claim True means assets should be compressed, which seems like
# more work, but it is 4x slower when False, maybe because it detects the
# existence of the file and skips generating a new one.
PIPELINE["PIPELINE_ENABLED"] = True

# The documents suggest this does nothing when PIPELINE_ENABLED=True. But,
# testing shows that tests run faster when set to True.
PIPELINE["PIPELINE_COLLECTOR_ENABLED"] = True

# We need the real Sass compiler here instead of the pass-through used for
# local dev.
PIPELINE["COMPILERS"] = ("pipeline.compilers.sass.SASSCompiler",)

# Testing with django-pipeline 1.6.8, PipelineStorage
# Enabled=T, Collector=T -   482s
# Enabled=T, Collector=F -   535s
# Enabled=F, Collector=T - 18262s
# Enabled=F, Collector=F -  2043s

# Defer to django-pipeline's finders for testing
# This avoids reading the static folder for each test client request, for
# a 10x speedup on Docker on MacOS.
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

# Never rely on the .env
GOOGLE_ANALYTICS_ACCOUNT = None

# Silence warnings about defaults that change in django-storages 2.0
AWS_BUCKET_ACL = None
AWS_DEFAULT_ACL = None

# Use a dedicated minio bucket for tests
ATTACHMENTS_AWS_STORAGE_BUCKET_NAME = "test"

# Never enabled in tests.
SENTRY_DSN = None

# To make absolutely sure we never accidentally trigger the GA tracking
# within tests to the actual (and default) www.google-analytics.com this is
# an extra safeguard.
GOOGLE_ANALYTICS_TRACKING_URL = "https://thisllneverwork.example.com/collect"

# Because that's what all the tests presume.
SITE_ID = 1

# Stripe API KEY settings
STRIPE_PUBLIC_KEY = "testing"
STRIPE_SECRET_KEY = "testing"
STRIPE_PLAN_ID = "testing"

# For legacy reasons, the tests assume these are always true so don't
# let local overrides take effect.
INDEX_HTML_ATTRIBUTES = True
INDEX_CSS_CLASSNAMES = True

# Amount for the monthly subscription.
# It's hardcoded here in case some test depends on the number and it futureproofs
# our tests to not deviate when the actual number changes since that number
# change shouldn't affect the tests.
CONTRIBUTION_AMOUNT_USD = 4.99

SENDINBLUE_API_KEY = "testing"
SENDINBLUE_LIST_ID = 7327

# This is False by default, to so we don't have to rewrite all the existing
# tests, it's True in this context.
ENABLE_SUBSCRIPTIONS = True
