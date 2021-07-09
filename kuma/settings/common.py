import json
from collections import namedtuple
from email.utils import parseaddr
from pathlib import Path

import dj_database_url
import sentry_sdk
from decouple import config, Csv
from sentry_sdk.integrations.django import DjangoIntegration


DEBUG = config("DEBUG", default=False, cast=bool)

BASE_DIR = Path(__file__).resolve().parent.parent

ADMIN_EMAILS = config("ADMIN_EMAILS", default="mdn-dev@mozilla.com", cast=Csv())
ADMINS = zip(config("ADMIN_NAMES", default="MDN devs", cast=Csv()), ADMIN_EMAILS)

PROTOCOL = config("PROTOCOL", default="https://")
DOMAIN = config("DOMAIN", default="developer.mozilla.org")
SITE_URL = config("SITE_URL", default=PROTOCOL + DOMAIN)
PRODUCTION_DOMAIN = "developer.mozilla.org"
PRODUCTION_URL = "https://" + PRODUCTION_DOMAIN
STAGING_DOMAIN = "developer.allizom.org"
STAGING_URL = "https://" + STAGING_DOMAIN

_PROD_INTERACTIVE_EXAMPLES = "https://interactive-examples.mdn.mozilla.net"
INTERACTIVE_EXAMPLES_BASE = config(
    "INTERACTIVE_EXAMPLES_BASE", default=_PROD_INTERACTIVE_EXAMPLES
)

MAINTENANCE_MODE = config("MAINTENANCE_MODE", default=False, cast=bool)
REVISION_HASH = config("REVISION_HASH", default="undefined")
MANAGERS = ADMINS


# # CONN_MAX_AGE: 'persistent' to keep open connection, or max seconds before
# # releasing. Default is 0 for a new connection per request.
# def parse_conn_max_age(value):
#     try:
#         return int(value)
#     except ValueError:
#         assert value.lower() == "persistent", 'Must be int or "persistent"'
#         return None


CONN_MAX_AGE = config("CONN_MAX_AGE", default=60)


DATABASES = {
    "default": config(
        "DATABASE_URL",
        default="postgresql://kuma:kuma@localhost/kuma",
        cast=dj_database_url.parse,
    )
}


SILENCED_SYSTEM_CHECKS = [
    # # https://django-mysql.readthedocs.io/en/latest/checks.html#django-mysql-w003-utf8mb4
    # "django_mysql.W003",
]

# Cache Settings
CACHE_PREFIX = "kuma"
CACHE_COUNT_TIMEOUT = 60  # in seconds

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "TIMEOUT": CACHE_COUNT_TIMEOUT * 60,
        "KEY_PREFIX": CACHE_PREFIX,
        "LOCATION": config("REDIS_CACHE_SERVER", default="127.0.0.1:6379"),
    }
}

# Email
# vars().update(config("EMAIL_URL", default="console://", cast=dj_email_url.parse))
EMAIL_SUBJECT_PREFIX = config("EMAIL_SUBJECT_PREFIX", default="[mdn]")
# Ensure EMAIL_SUBJECT_PREFIX has one trailing space
EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX.strip() + " "

# Addresses email comes from
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL", default="notifications@developer.mozilla.org"
)
SERVER_EMAIL = config("SERVER_EMAIL", default="server-error@developer.mozilla.org")

# PLATFORM_NAME = platform.node()

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "UTC"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-US"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Accepted locales.
# The order of some codes is important. For example, 'pt-PT' comes before
# 'pt-BR', so that 'pt-PT' will be selected when the generic 'pt' is requested.
# Candidate locales should be included here and in CANDIDATE_LOCALES
ACCEPTED_LOCALES = (
    "en-US",  # English
    "de",  # German
    "es",  # Spanish
    "fr",  # French
    "ja",  # Japanese
    "ko",  # Korean
    "pl",  # Polish
    "pt-BR",  # Portuguese (Brazil)
    "ru",  # Russian
    "zh-CN",  # Chinese (China)
    "zh-TW",  # Chinese (Taiwan, Province of China)
)

# When there are multiple options for a given language, this gives the
# preferred locale for that language (language => preferred locale).
PREFERRED_LOCALE = {
    "zh": "zh-CN",
}

# Locales being considered for MDN. This makes the UI strings available for
# localization in Pontoon, but pages can not be translated into this language.
# https://developer.mozilla.org/en-US/docs/MDN/Contribute/Localize/Starting_a_localization
# These should be here and in the ACCEPTED_LOCALES list
CANDIDATE_LOCALES = ()
# Asserted here to avoid a unit test that is skipped when empty
for candidate in CANDIDATE_LOCALES:
    assert candidate in ACCEPTED_LOCALES

ENABLE_CANDIDATE_LANGUAGES = config(
    "ENABLE_CANDIDATE_LANGUAGES", default=DEBUG, cast=bool
)

if ENABLE_CANDIDATE_LANGUAGES:
    ENABLED_LOCALES = ACCEPTED_LOCALES[:]
else:
    ENABLED_LOCALES = [
        locale for locale in ACCEPTED_LOCALES if locale not in CANDIDATE_LOCALES
    ]

# Override generic locale handling with explicit mappings.
# Keys are the requested locale (lowercase); values are the delivered locale.
LOCALE_ALIASES = {
    # Create aliases for over-specific locales.
    "cn": "zh-CN",
    # Create aliases for locales which use region subtags to assume scripts.
    "zh-hans": "zh-CN",
    "zh-hant": "zh-TW",
    # Map locale whose region subtag is separated by `_`(underscore)
    "zh_cn": "zh-CN",
    "zh_tw": "zh-TW",
}

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in ENABLED_LOCALES])

for requested_lang, delivered_lang in LOCALE_ALIASES.items():
    if delivered_lang in ENABLED_LOCALES:
        LANGUAGE_URL_MAP[requested_lang.lower()] = delivered_lang


def _get_locales():
    """
    Load LOCALES data from languages.json

    languages.json is from the product-details project:
    https://product-details.mozilla.org/1.0/languages.json
    """
    lang_path = BASE_DIR / "settings" / "languages.json"
    with open(lang_path) as lang_file:
        json_locales = json.load(lang_file)

    locales = {}
    _Language = namedtuple("Language", "english native")
    for locale, meta in json_locales.items():
        locales[locale] = _Language(meta["English"], meta["native"])
    return locales


LOCALES = _get_locales()
LANGUAGES = [(locale, LOCALES[locale].native) for locale in ENABLED_LOCALES]

# Language list sorted for forms (English, then alphabetical by locale code)
SORTED_LANGUAGES = [LANGUAGES[0]] + sorted(LANGUAGES[1:])

LANGUAGE_COOKIE_NAME = "preferredlocale"
# The number of seconds we are keeping the language preference cookie. (3 years)
LANGUAGE_COOKIE_AGE = 3 * 365 * 24 * 60 * 60
LANGUAGE_COOKIE_SECURE = "localhost" not in DOMAIN

SITE_ID = config("SITE_ID", default=1, cast=int)


STATIC_URL = config("STATIC_URL", default="/static/")

SERVE_MEDIA = False

# Paths that don't require a locale prefix.
LANGUAGE_URL_IGNORED_PATHS = (
    "healthz",
    "readiness",
    "media",
    "admin",
    "robots.txt",
    "contribute.json",
    "services",
    "static",
    "1",
    "files",
    "@api",
    "__debug__",
    ".well-known",
    "users/github/login/callback/",
    "favicon.ico",
    "_kuma_status.json",
    # Legacy files, circa 2008, served in AWS
    "diagrams",
    "presentations",
    "samples",
    # Legacy files, circa 2008, now return 404
    "patches",
    "web-tech",
    "css",
    "index.php",  # Legacy MediaWiki endpoint, return 404
    "i18n",
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config(
    "SECRET_KEY", default="#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z"
)


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kuma.urls"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # MDN
    "kuma.core.apps.CoreConfig",
    "kuma.wiki.apps.WikiConfig",
    "kuma.api.apps.APIConfig",
    "kuma.attachments.apps.AttachmentsConfig",
    "kuma.plus.apps.PlusConfig",
    # 3rd party
    "django_extensions",
]


# # TODO: Figure out why changing the order of apps (for example, moving taggit
# # higher in the list) breaks tests.
# INSTALLED_APPS = (
#     # django
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.sites",
#     "django.contrib.admin",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     # MDN
#     "kuma.core.apps.CoreConfig",
#     "kuma.landing",
#     "kuma.search.apps.SearchConfig",
#     "kuma.users.apps.UserConfig",
#     "kuma.wiki.apps.WikiConfig",
#     "kuma.api.apps.APIConfig",
#     "kuma.attachments.apps.AttachmentsConfig",
#     "allauth",
#     "allauth.account",
#     "allauth.socialaccount",
#     "kuma.users.providers.github",
#     "kuma.users.providers.google",
#     "kuma.plus.apps.PlusConfig",
#     # util
#     "django_jinja",
#     "puente",
#     "waffle",
#     "kuma.authkeys",
#     "taggit",
#     "django_extensions",
#     "statici18n",
#     "rest_framework",
#     "rest_framework.authtoken",
#     "django_mysql",
# )


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Session cookies
SESSION_COOKIE_DOMAIN = DOMAIN
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=60 * 60 * 24 * 365, cast=int)

# WAFFLE_SECURE = config("WAFFLE_COOKIE_SECURE", default=True, cast=bool)
# # This is a setting unique to Kuma which specifies the domain
# # that will be used for all of the waffle cookies. It is used by
# # kuma.core.middleware.WaffleWithCookieDomainMiddleware.
# WAFFLE_COOKIE_DOMAIN = DOMAIN

# bug 856061
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="developer-local.allizom.org, mdn-local.mozillademos.org",
    cast=Csv(),
)

_PROD_ATTACHMENT_HOST = "mdn.mozillademos.org"
_PROD_ATTACHMENT_SITE_URL = "https://" + _PROD_ATTACHMENT_HOST
ATTACHMENT_HOST = config("ATTACHMENT_HOST", default=_PROD_ATTACHMENT_HOST)
ATTACHMENT_SITE_URL = PROTOCOL + ATTACHMENT_HOST
_PROD_ATTACHMENT_ORIGIN = "demos-origin.mdn.mozit.cloud"
ATTACHMENT_ORIGIN = config("ATTACHMENT_ORIGIN", default=_PROD_ATTACHMENT_ORIGIN)

# Primary use case if for file attachments that are still served via Kuma.
# We have settings.ATTACHMENTS_USE_S3 on by default. So a URL like
# `/files/3710/Test_Form_2.jpg` will trigger a 302 response (to its final
# public S3 URL). This 302 response can be cached in the CDN. That's what
# this setting controls.
# We can make it pretty aggressive, because as of early 2021, you can't
# edit images by uploading a different one through the Wiki UI.
ATTACHMENTS_CACHE_CONTROL_MAX_AGE = config(
    "ATTACHMENTS_CACHE_CONTROL_MAX_AGE", default=60 * 60 * 24, cast=int
)

# This should never be false for the production and stage deployments.
ENABLE_RESTRICTIONS_BY_HOST = config(
    "ENABLE_RESTRICTIONS_BY_HOST", default=True, cast=bool
)

# Allow robots, but restrict some paths
# If the domain is a CDN, the CDN origin should be included.
ALLOW_ROBOTS_WEB_DOMAINS = set(
    config(
        "ALLOW_ROBOTS_WEB_DOMAINS",
        default="developer.mozilla.org",
        cast=Csv(),
    )
)

# Allow robots, no path restrictions
# If the domain is a CDN, the CDN origin should be included.
ALLOW_ROBOTS_DOMAINS = set(
    config(
        "ALLOW_ROBOTS_DOMAINS",
        default=",".join((_PROD_ATTACHMENT_HOST, _PROD_ATTACHMENT_ORIGIN)),
        cast=Csv(),
    )
)


# Email
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.filebased.EmailBackend"
)
EMAIL_FILE_PATH = "/app/tmp/emails"

# Celery (asynchronous tasks)
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://0.0.0.0:6379/0")

CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", False, cast=bool)
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_WORKER_CONCURRENCY = config("CELERY_WORKER_CONCURRENCY", default=4, cast=int)

# Maximum tasks run before auto-restart of child process,
# to mitigate memory leaks. None / 0 means unlimited tasks
CELERY_WORKER_MAX_TASKS_PER_CHILD = (
    config("CELERY_WORKER_MAX_TASKS_PER_CHILD", default=0, cast=int) or None
)

# Sadly, kuma depends on pickle being the default serializer.
# In Celery 4, the default is now JSON.
# It's probably too late to switch all tasks to work with either.
# Just remember, avoid passing types that are non-trivial and is
# different in pickle vs json. Keep things simple. Even if it means
# you have to do type conversions in the tasks' code.
CELERY_ACCEPT_CONTENT = ["pickle", "application/x-python-serialize"]
CELERY_TASK_SERIALIZER = "pickle"
CELERY_RESULT_SERIALIZER = "pickle"
CELERY_EVENT_SERIALIZER = "pickle"

CELERY_TASK_ROUTES = {
    "kuma.core.tasks.clean_sessions": {"queue": "mdn_purgeable"},
}

# Do not change this without also deleting all wiki documents:
# WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE


# Number of expired sessions to cleanup up in one go.
SESSION_CLEANUP_CHUNK_SIZE = config(
    "SESSION_CLEANUP_CHUNK_SIZE", default=1000, cast=int
)

# Email address from which welcome emails will be sent
WELCOME_EMAIL_FROM = config(
    "WELCOME_EMAIL_FROM",
    default="MDN team <mdn-admins@mozilla.org>",
)
# If this fails, SMTP will probably also fail.
# E.g. https://github.com/mdn/kuma/issues/7121
assert parseaddr(WELCOME_EMAIL_FROM)[1].count("@") == 1, parseaddr(WELCOME_EMAIL_FROM)

# Email address to request admin intervention
EMAIL_LIST_MDN_ADMINS = config(
    "EMAIL_LIST_MDN_ADMINS", default="mdn-admins@mozilla.org"
)

# Elasticsearch related settings.
# XXX Peter: Need to audit which of these we actually use!
ES_DEFAULT_NUM_REPLICAS = 1
ES_DEFAULT_NUM_SHARDS = 5
ES_DEFAULT_REFRESH_INTERVAL = "5s"
ES_INDEX_PREFIX = config("ES_INDEX_PREFIX", default="mdn")
ES_INDEXES = {"default": "main_index"}
# Specify the extra timeout in seconds for the indexing ES connection.
ES_INDEXING_TIMEOUT = 30
ES_LIVE_INDEX = config("ES_LIVE_INDEX", default=False, cast=bool)
ES_URLS = config("ES_URLS", default="127.0.0.1:9200", cast=Csv())
# Specify a max length for the q param to avoid unnecessary burden on
# elasticsearch for queries that are probably either mistakes or junk.
ES_Q_MAXLENGTH = config("ES_Q_MAXLENGTH", default=200, cast=int)
ES_RETRY_SLEEPTIME = config("ES_RETRY_SLEEPTIME", default=1, cast=int)
ES_RETRY_ATTEMPTS = config("ES_RETRY_ATTEMPTS", default=5, cast=int)
ES_RETRY_JITTER = config("ES_RETRY_JITTER", default=1, cast=int)

# Logging is merged with the default logging
# https://github.com/django/django/blob/stable/1.11.x/django/utils/log.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}},
    "formatters": {"simple": {"format": "%(name)s:%(levelname)s %(message)s"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "console-simple": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},  # Drop mail_admins
        "kuma": {"handlers": ["console-simple"], "propagate": True, "level": "ERROR"},
        "elasticsearch": {
            "handlers": ["console-simple"],
            "level": config("ES_LOG_LEVEL", default="ERROR"),
        },
        "elasticsearch.trace": {
            "handlers": ["console-simple"],
            "level": config("ES_TRACE_LOG_LEVEL", default="ERROR"),
            "propagate": False,
        },
        "urllib3": {"handlers": ["console-simple"], "level": "ERROR"},
    },
}

CSRF_COOKIE_DOMAIN = DOMAIN
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
# We need to explcitly set the trusted origins, because when CSRF_COOKIE_DOMAIN
# is explicitly set, as we do above, Django's CsrfViewMiddleware will reject
# the request unless the domain of the incoming referer header matches not just
# the CSRF_COOKIE_DOMAIN alone, but the CSRF_COOKIE_DOMAIN with the server port
# appended as well, and we don't want that behavior (a server port of 8000 is
# added both in secure local development as well as in K8s stage/production, so
# that will guarantee a mismatch with the referer).
CSRF_TRUSTED_ORIGINS = [DOMAIN]
X_FRAME_OPTIONS = "DENY"


# Caching constants for the Cache-Control header.
CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE = config(
    "CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE", default=60 * 5, cast=int
)


# Setting for configuring the AWS S3 bucket name used for the document API.
MDN_API_S3_BUCKET_NAME = config("MDN_API_S3_BUCKET_NAME", default=None)

# Serve and upload attachments via S3, instead of the local filesystem
ATTACHMENTS_USE_S3 = config("ATTACHMENTS_USE_S3", default=False, cast=bool)

# AWS S3 credentials and settings for uploading attachments
ATTACHMENTS_AWS_ACCESS_KEY_ID = config("ATTACHMENTS_AWS_ACCESS_KEY_ID", default=None)
ATTACHMENTS_AWS_SECRET_ACCESS_KEY = config(
    "ATTACHMENTS_AWS_SECRET_ACCESS_KEY", default=None
)
ATTACHMENTS_AWS_STORAGE_BUCKET_NAME = config(
    "ATTACHMENTS_AWS_STORAGE_BUCKET_NAME", default="media"
)

ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN = config(
    "ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN", default="media.prod.mdn.mozit.cloud"
)  # For example, Cloudfront CDN domain
ATTACHMENTS_AWS_S3_SECURE_URLS = config(
    "ATTACHMENTS_AWS_S3_SECURE_URLS", default=True, cast=bool
)  # Does the custom domain use TLS
ATTACHMENTS_AWS_S3_CUSTOM_URL = f"{'https' if ATTACHMENTS_AWS_S3_SECURE_URLS else 'http'}://{ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN}"

ATTACHMENTS_AWS_S3_REGION_NAME = config(
    "ATTACHMENTS_AWS_S3_REGION_NAME", default="us-east-1"
)
ATTACHMENTS_AWS_S3_ENDPOINT_URL = config(
    "ATTACHMENTS_AWS_S3_ENDPOINT_URL", default=None
)


# Kuma doesn't index anything, that's done by the Yari Deployer, but we need
# to know what the index is called for searching.
SEARCH_INDEX_NAME = config("SEARCH_INDEX_NAME", default="mdn_docs")

PLUS_VARIANTS = config(
    "PLUS_VARIANTS_JSON",
    default=json.dumps(
        [
            "$X a month or $XX a year",
            "$Y a month or $YY a year",
        ]
    ),
    cast=json.loads,
)


SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
    )
