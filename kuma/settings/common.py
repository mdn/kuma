# Django settings for kuma project.
import json
import os
import platform
import re
from collections import namedtuple
from email.utils import parseaddr
from os.path import dirname
from urllib.parse import urlsplit

import dj_database_url
import dj_email_url
from decouple import config, Csv

_Language = namedtuple("Language", "english native")


def path(*parts):
    return os.path.join(BASE_DIR, *parts)


DEBUG = config("DEBUG", default=False, cast=bool)

# BASE_DIR used by django-extensions, such as ./manage.py notes
# ROOT used by some Kuma application code
BASE_DIR = ROOT = dirname(dirname(dirname(os.path.abspath(__file__))))

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


# CONN_MAX_AGE: 'persistent' to keep open connection, or max seconds before
# releasing. Default is 0 for a new connection per request.
def parse_conn_max_age(value):
    try:
        return int(value)
    except ValueError:
        assert value.lower() == "persistent", 'Must be int or "persistent"'
        return None


CONN_MAX_AGE = config("CONN_MAX_AGE", default=60, cast=parse_conn_max_age)
DEFAULT_DATABASE = config(
    "DATABASE_URL",
    default="mysql://kuma:kuma@localhost:3306/kuma",
    cast=dj_database_url.parse,
)


if "mysql" in DEFAULT_DATABASE["ENGINE"]:
    # These are the production settings for OPTIONS.
    DEFAULT_DATABASE.update(
        {
            "CONN_MAX_AGE": CONN_MAX_AGE,
            "OPTIONS": {
                "charset": "utf8",
                "use_unicode": True,
                "init_command": "SET "
                "innodb_strict_mode=1,"
                "storage_engine=INNODB,"
                "sql_mode='STRICT_TRANS_TABLES',"
                "character_set_connection=utf8,"
                "collation_connection=utf8_general_ci",
            },
            "TEST": {"CHARSET": "utf8", "COLLATION": "utf8_general_ci"},
        }
    )

DATABASES = {
    "default": DEFAULT_DATABASE,
}


SILENCED_SYSTEM_CHECKS = [
    # https://django-mysql.readthedocs.io/en/latest/checks.html#django-mysql-w003-utf8mb4
    "django_mysql.W003",
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
vars().update(config("EMAIL_URL", default="console://", cast=dj_email_url.parse))
EMAIL_SUBJECT_PREFIX = config("EMAIL_SUBJECT_PREFIX", default="[mdn]")
# Ensure EMAIL_SUBJECT_PREFIX has one trailing space
EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX.strip() + " "

# Addresses email comes from
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL", default="notifications@developer.mozilla.org"
)
SERVER_EMAIL = config("SERVER_EMAIL", default="server-error@developer.mozilla.org")

PLATFORM_NAME = platform.node()

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "US/Pacific"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-US"

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
    lang_path = path("kuma", "settings", "languages.json")
    with open(lang_path, "r") as lang_file:
        json_locales = json.load(lang_file)

    locales = {}
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

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = (path("locale"),)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = config("MEDIA_ROOT", default=path("media"))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = config("MEDIA_URL", default="/media/")

STATIC_URL = config("STATIC_URL", default="/static/")
STATIC_ROOT = path("static")

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


_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.request",
    "django.template.context_processors.csrf",
    "django.contrib.messages.context_processors.messages",
    "kuma.core.context_processors.global_settings",
    "kuma.core.context_processors.i18n",
    "kuma.core.context_processors.next_url",
)


MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "kuma.core.middleware.SetRemoteAddrFromForwardedFor",
    (
        "kuma.core.middleware.ForceAnonymousSessionMiddleware"
        if MAINTENANCE_MODE
        else "django.contrib.sessions.middleware.SessionMiddleware"
    ),
    "kuma.core.middleware.LocaleStandardizerMiddleware",
    # LocaleMiddleware must be before any middleware that uses
    # kuma.core.urlresolvers.reverse() to add locale prefixes to URLs:
    "kuma.core.middleware.LocaleMiddleware",
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

if not MAINTENANCE_MODE:
    # We don't want this in maintence mode, as it adds "Cookie"
    # to the Vary header, which in turn, kills caching.
    MIDDLEWARE += ("django.middleware.csrf.CsrfViewMiddleware",)

MIDDLEWARE += (
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "kuma.core.middleware.WaffleWithCookieDomainMiddleware",
)

ENABLE_QUERYCOUNT = config("ENABLE_QUERYCOUNT", default=False, cast=bool)
if ENABLE_QUERYCOUNT:
    # Prints heavy query counts per request.
    QUERYCOUNT = {
        "IGNORE_REQUEST_PATTERNS": [r"^/admin/"],
        "DISPLAY_DUPLICATES": config(
            "QUERYCOUNT_DISPLAY_DUPLICATES", cast=int, default=0
        ),
    }
    MIDDLEWARE += ("querycount.middleware.QueryCountMiddleware",)

# Auth
AUTHENTICATION_BACKENDS = (
    "kuma.users.auth_backends.KumaAuthBackend",  # Handles User Bans
    "allauth.account.auth_backends.AuthenticationBackend",  # Legacy
)
AUTH_USER_MODEL = "users.User"

if urlsplit(STATIC_URL).hostname in (None, "localhost"):
    # Avatar needs a publicly available default image
    DEFAULT_AVATAR = PRODUCTION_URL + "/static/img/avatar.png"
else:
    DEFAULT_AVATAR = STATIC_URL + "img/avatar.png"

ROOT_URLCONF = "kuma.urls"

STATICFILES_DIRS = [
    path("build", "locale"),
]

# TODO: Figure out why changing the order of apps (for example, moving taggit
# higher in the list) breaks tests.
INSTALLED_APPS = (
    # django
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # MDN
    "kuma.core.apps.CoreConfig",
    "kuma.landing",
    "kuma.search.apps.SearchConfig",
    "kuma.users.apps.UserConfig",
    "kuma.wiki.apps.WikiConfig",
    "kuma.api.apps.APIConfig",
    "kuma.attachments.apps.AttachmentsConfig",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "kuma.users.providers.github",
    "kuma.users.providers.google",
    "kuma.users.newsletter.apps.UserNewsletterConfig",
    "kuma.plus.apps.PlusConfig",
    # util
    "django_jinja",
    "puente",
    "waffle",
    "kuma.authkeys",
    "taggit",
    "django_extensions",
    "statici18n",
    "rest_framework",
    "rest_framework.authtoken",
    "django_mysql",
)

TEMPLATES = [
    {
        "NAME": "jinja2",
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": [path("jinja2"), path("static")],
        "APP_DIRS": True,
        "OPTIONS": {
            # Use jinja2/ for jinja templates
            "app_dirname": "jinja2",
            # Don't figure out which template loader to use based on
            # file extension
            "match_extension": "",
            "newstyle_gettext": True,
            "context_processors": _CONTEXT_PROCESSORS,
            "undefined": "jinja2.Undefined",
            "extensions": [
                "jinja2.ext.do",
                "jinja2.ext.loopcontrols",
                "jinja2.ext.i18n",
                "puente.ext.i18n",
                "django_jinja.builtins.extensions.CsrfExtension",
                "django_jinja.builtins.extensions.CacheExtension",
                "django_jinja.builtins.extensions.TimezoneExtension",
                "django_jinja.builtins.extensions.UrlsExtension",
                "django_jinja.builtins.extensions.StaticFilesExtension",
                "django_jinja.builtins.extensions.DjangoFiltersExtension",
                "waffle.jinja.WaffleExtension",
                "kuma.core.i18n.TranslationExtension",
            ],
        },
    },
    {
        "NAME": "django",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [path("templates")],
        "APP_DIRS": False,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": _CONTEXT_PROCESSORS,
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

PUENTE = {
    "VERSION": "2020.32",
    "BASE_DIR": BASE_DIR,
    "TEXT_DOMAIN": "django",
    # Tells the extract script what files to look for l10n in and what function
    # handles the extraction.
    "DOMAIN_METHODS": {
        "django": [
            ("kuma/**.py", "python"),
            ("**/templates/**.html", "enmerkar.extract.extract_django"),
            ("**/jinja2/**.html", "jinja2"),
            ("**/jinja2/**.ltxt", "jinja2"),
        ],
    },
    "PROJECT": "MDN",
    "MSGID_BUGS_ADDRESS": ADMIN_EMAILS[0],
}

STATICI18N_ROOT = "build/locale"
STATICI18N_DOMAIN = "javascript"

# Cache non-versioned static files for one week
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 7

# Session cookies
SESSION_COOKIE_DOMAIN = DOMAIN
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=60 * 60 * 24 * 365, cast=int)

WAFFLE_SECURE = config("WAFFLE_COOKIE_SECURE", default=True, cast=bool)
# This is a setting unique to Kuma which specifies the domain
# that will be used for all of the waffle cookies. It is used by
# kuma.core.middleware.WaffleWithCookieDomainMiddleware.
WAFFLE_COOKIE_DOMAIN = DOMAIN

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


# Allowed iframe URL patterns
# The format is a three-element tuple:
#  Protocol: Required, must match
#  Domain: Required, must match
#  Path: An optional path prefix or matching regex


def parse_iframe_url(url):
    """
    Parse an iframe URL into an allowed iframe pattern

    A URL with a '*' in the path is treated as a regex.
    """
    parts = urlsplit(url)
    assert parts.scheme in ("http", "https")
    path = ""
    if parts.path.strip("/") != "":
        if "*" in parts.path:
            path = re.compile(parts.path)
        else:
            path = parts.path
    return (parts.scheme, parts.netloc, path)


# Default allowed iframe URL patterns, roughly ordered by expected frequency
ALLOWED_IFRAME_PATTERNS = [
    # Live sample host
    # https://developer.mozilla.org/en-US/docs/Web/CSS/filter
    parse_iframe_url(_PROD_ATTACHMENT_SITE_URL),
    # Interactive Examples host
    # On https://developer.mozilla.org/en-US/docs/Web/CSS/filter
    parse_iframe_url(_PROD_INTERACTIVE_EXAMPLES),
    # Samples, https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial/Getting_started_with_WebGL
    parse_iframe_url("https://mdn.github.io/"),
    # Videos, https://developer.mozilla.org/en-US/docs/Tools/Web_Console
    parse_iframe_url("https://www.youtube.com/embed/"),
    # Samples, https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures
    parse_iframe_url("https://jsfiddle.net/.*/embedded/.*"),
    # Charts, https://developer.mozilla.org/en-US/docs/MDN/Kuma/Server_charts
    parse_iframe_url("https://rpm.newrelic.com/public/charts/"),
    # Test262 Report, https://test262.report/
    parse_iframe_url("https://test262.report/embed/features/"),
]

# Add the overridden attachment / live sample host
if ATTACHMENT_SITE_URL != _PROD_ATTACHMENT_SITE_URL:
    ALLOWED_IFRAME_PATTERNS.append(parse_iframe_url(ATTACHMENT_SITE_URL))

# Add the overridden interactive examples service
if INTERACTIVE_EXAMPLES_BASE != _PROD_INTERACTIVE_EXAMPLES:
    ALLOWED_IFRAME_PATTERNS.append(parse_iframe_url(INTERACTIVE_EXAMPLES_BASE))

# Add more iframe patterns from the environment
_ALLOWED_IFRAME_PATTERNS = config("ALLOWED_IFRAME_PATTERNS", default="", cast=Csv())
for pattern in _ALLOWED_IFRAME_PATTERNS:
    ALLOWED_IFRAME_PATTERNS.append(parse_iframe_url(pattern))

# Allow all iframe sources (for debugging)
ALLOW_ALL_IFRAMES = config("ALLOW_ALL_IFRAMES", default=False, cast=bool)


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
    "kuma.users.tasks.send_welcome_email": {"queue": "mdn_emails"},
}

# Do not change this without also deleting all wiki documents:
WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE

# Number of days to keep the trashed attachments files before they are removed from
# the file storage.
WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS = config(
    "WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS", default=14, cast=int
)

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

# Name of the django.contrib.auth.models.Group to use as beta testers
BETA_GROUP_NAME = config("BETA_GROUP_NAME", default="Beta Testers")

# Email address to notify of possible spam (first edits, blocked edits)
EMAIL_LIST_SPAM_WATCH = config(
    "EMAIL_LIST_SPAM_WATCH", default="mdn-spam-watch@mozilla.com"
)

# Google Analytics Tracking Account Number (0 to disable)
GOOGLE_ANALYTICS_ACCOUNT = config("GOOGLE_ANALYTICS_ACCOUNT", default=None)

# When HTTP posting event to Google Analytics this is the combined connect
# and read timeout.
GOOGLE_ANALYTICS_TRACKING_TIMEOUT = config(
    "GOOGLE_ANALYTICS_TRACKING_TIMEOUT", cast=float, default=2.0
)
# The only reason you'd want to override this is for local development where
# you might want to substitute the events tracking URL to a local dev server.
# https://developers.google.com/analytics/devguides/collection/protocol/v1/reference
GOOGLE_ANALYTICS_TRACKING_URL = config(
    "GOOGLE_ANALYTICS_TRACKING_URL", default="https://www.google-analytics.com/collect"
)
# This setting only really makes sense for the benefit of Django unit tests.
# All tests are run with `settings.DEBUG === False` so we can't rely on that
# for *avoid* any errors swallowed. And in tests we don't want to swallow
# any `requests` errors because most possibly they happen because we
# incorrectly mocked requests.
GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = config(
    "GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS", cast=bool, default=DEBUG
)

# Elasticsearch related settings.
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


def get_user_url(user):
    from kuma.core.urlresolvers import reverse

    return reverse("users.user_detail", args=[user.username])


ABSOLUTE_URL_OVERRIDES = {"users.user": get_user_url}

# Set header X-XSS-Protection: 1; mode=block
SECURE_BROWSER_XSS_FILTER = True

# Set header X-Content-Type-Options: nosniff
SECURE_CONTENT_TYPE_NOSNIFF = True

# Set header Strict-Transport-Security header
# 63072000 in production (730 days)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)

# Honor the X-Forwarded-Proto header, to assume HTTPS instead of HTTP
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# django-allauth configuration
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = config("ACCOUNT_DEFAULT_HTTP_PROTOCOL", default="https")
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_ADAPTER = "kuma.users.adapters.KumaAccountAdapter"
ACCOUNT_SIGNUP_FORM_CLASS = None
ACCOUNT_UNIQUE_EMAIL = False

SOCIALACCOUNT_ADAPTER = "kuma.users.adapters.KumaSocialAccountAdapter"
SOCIALACCOUNT_EMAIL_VERIFICATION = "mandatory"
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = False  # forces the use of the signup view
SOCIALACCOUNT_QUERY_EMAIL = True  # used by the custom github provider

BLOCKABLE_USER_AGENTS = [
    "Yahoo! Slurp",
    "Googlebot",
    "bingbot",
    "Applebot",
    "YandexBot",
    "Baiduspider",
    "CCBot",
    "ScoutJet",
    "wget",
    "curl",
]

# Tell django-taggit to use case-insensitive search for existing tags
TAGGIT_CASE_INSENSITIVE = True

# Ad Banner Settings
NEWSLETTER = True
NEWSLETTER_ARTICLE = True

# Auth and permissions related constants
LOGIN_URL = "/signin"
LOGIN_REDIRECT_URL = "/"

# Caching constants for the Cache-Control header.
CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE = config(
    "CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE", default=60 * 5, cast=int
)

# Stripe API KEY settings
STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_PLAN_ID = config("STRIPE_PLAN_ID", default="")
# Misc Stripe settings
STRIPE_MAX_NETWORK_RETRIES = config("STRIPE_MAX_NETWORK_RETRIES", default=5, cast=int)

CONTRIBUTION_SUPPORT_EMAIL = config(
    "CONTRIBUTION_SUPPORT_EMAIL", default="mdn-support@mozilla.com"
)

# The default amount suggested for monthly subscription payments.
# As of March 2020, we only have 1 plan and the number is fixed.
# In the future, we might have multiple plans and this might a dict of amount
# per plan.
# The reason it's not an environment variable is to simply indicate that it
# can't be overridden at the moment based on the environment.
CONTRIBUTION_AMOUNT_USD = 5.0

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
    "ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN", default=None
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

# Silence warnings about defaults that change in django-storages 2.0
AWS_BUCKET_ACL = None
AWS_DEFAULT_ACL = None

# html_attributes and css_classnames get indexed into Elasticsearch on every
# document when sent in. These can be very memory consuming since the
# 'html_attributes' makes up about 60% of the total weight.
# Refer to this GitHub issue for an estimate of their weight contribution:
# https://github.com/mdn/kuma/issues/6264#issue-539922604
# Note that the only way to actually search on these fields is with a manual
# use of the search v1 API. There is no UI at all for searching on something
# in the 'html_attributes' or the 'css_classnames'.
# By disabling indexing of these, in your local dev environment, your local
# Elasticsearch instance will be a LOT smaller.
INDEX_HTML_ATTRIBUTES = config("INDEX_HTML_ATTRIBUTES", cast=bool, default=not DEBUG)
INDEX_CSS_CLASSNAMES = config("INDEX_CSS_CLASSNAMES", cast=bool, default=not DEBUG)

# For local development you might want to set this to a hostname provided to
# you by a tunneling service such as ngrok.
CUSTOM_WEBHOOK_HOSTNAME = config("CUSTOM_WEBHOOK_HOSTNAME", default=None)

# We use sendinblue.com to send marketing emails and are subdividing users
# into lists of paying and not paying users
SENDINBLUE_API_KEY = config("SENDINBLUE_API_KEY", default=None)
SENDINBLUE_LIST_ID = config("SENDINBLUE_LIST_ID", default=None)

# When doing local development with Yari, if you want to have `?next=...` redirects
# work when you sign in on Yari, this needs to be set to `localhost.org:3000` in your
# .env file. That tells, Kuma that if the `?next` URL is an absolute URL, that
# it's safe to use and redirect to.
# This additional host is always, also, dependent on settings.DEBUG==True.
ADDITIONAL_NEXT_URL_ALLOWED_HOSTS = config(
    "ADDITIONAL_NEXT_URL_ALLOWED_HOSTS", default=None
)

# As of Oct 2020, we might not enable subscriptions at all. There are certain
# elements of Kuma that exposes subscriptions even if all the Waffle flags and
# switches says otherwise. For example, the payments pages are skeletons for
# React apps. This boolean settings disables all of that.
ENABLE_SUBSCRIPTIONS = config("ENABLE_SUBSCRIPTIONS", cast=bool, default=False)

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
