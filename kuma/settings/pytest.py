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

# SHA1 because it is fast, and hard-coded in the test fixture JSON.
PASSWORD_HASHERS = ("django.contrib.auth.hashers.SHA1PasswordHasher",)

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


# Always assume we prefer https.
PROTOCOL = "https://"

# Never rely on the .env
GOOGLE_ANALYTICS_ACCOUNT = None

# Silence warnings about defaults that change in django-storages 2.0
AWS_BUCKET_ACL = None
AWS_DEFAULT_ACL = None

# Use a dedicated minio bucket for tests
ATTACHMENTS_AWS_STORAGE_BUCKET_NAME = "test"

# To make absolutely sure we never accidentally trigger the GA tracking
# within tests to the actual (and default) www.google-analytics.com this is
# an extra safeguard.
GOOGLE_ANALYTICS_TRACKING_URL = "https://thisllneverwork.example.com/collect"

# Because that's what all the tests presume.
SITE_ID = 1

# Stripe API KEY settings
STRIPE_PUBLIC_KEY = "testing"
STRIPE_SECRET_KEY = "testing"
STRIPE_PRICE_IDS = ["price_0000001", "price_0000002"]

# For legacy reasons, the tests assume these are always true so don't
# let local overrides take effect.
INDEX_HTML_ATTRIBUTES = True
INDEX_CSS_CLASSNAMES = True

# Amount for the monthly subscription.
# It's hardcoded here in case some test depends on the number and it futureproofs
# our tests to not deviate when the actual number changes since that number
# change shouldn't affect the tests.
CONTRIBUTION_AMOUNT_USD = 4.99

# So it never accidentally actually uses the real value
BOOKMARKS_BASE_URL = "https://developer.example.com"

# OIDC related
OIDC_CONFIGURATION_CHECK = True
OIDC_RP_CLIENT_ID = "123456789"
OIDC_RP_CLIENT_SECRET = "xyz-secret-123"
OIDC_CONFIGURATION_URL = "https://accounts.examples.com"
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{OIDC_CONFIGURATION_URL}/authorization"

OIDC_OP_TOKEN_ENDPOINT = f"{OIDC_CONFIGURATION_URL}/v1/token"
OIDC_OP_USER_ENDPOINT = f"{OIDC_CONFIGURATION_URL}/v1/profile"
OIDC_OP_JWKS_ENDPOINT = f"{OIDC_CONFIGURATION_URL}/v1/jwks"
OIDC_RP_SIGN_ALGO = "XYZ"
OIDC_USE_NONCE = False
OIDC_RP_SCOPES = "openid profile email"

SUBSCRIPTION_SUBSCRIBE_URL = "https://accounts.example.com/subscriptions/products/"
SUBSCRIPTION_SETTINGS_URL = "https://accounts.example.com/subscriptions/settings/"
SUBPLAT_CONFIGURATION_CHECK = True
