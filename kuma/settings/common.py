# Django settings for kuma project.
import json
import os
import platform
import re
from collections import namedtuple
from os.path import dirname

import dj_database_url
import dj_email_url
from decouple import config, Csv
from six.moves.urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

_Language = namedtuple(u'Language', u'english native')


def path(*parts):
    return os.path.join(BASE_DIR, *parts)


class TupleCsv(Csv):

    def __call__(self, value):
        split_values = super(TupleCsv, self).__call__(value)
        return tuple((value, value) for value in split_values)


DEBUG = config('DEBUG', default=False, cast=bool)

# BASE_DIR used by django-extensions, such as ./manage.py notes
# ROOT used by some Kuma application code
BASE_DIR = ROOT = dirname(dirname(dirname(os.path.abspath(__file__))))

ADMIN_EMAILS = config('ADMIN_EMAILS', default='mdn-dev@mozilla.com',
                      cast=Csv())
ADMINS = zip(
    config('ADMIN_NAMES', default='MDN devs', cast=Csv()),
    ADMIN_EMAILS
)

PROTOCOL = config('PROTOCOL', default='https://')
DOMAIN = config('DOMAIN', default='developer.mozilla.org')
SITE_URL = config('SITE_URL', default=PROTOCOL + DOMAIN)
PRODUCTION_DOMAIN = 'developer.mozilla.org'
PRODUCTION_URL = 'https://' + PRODUCTION_DOMAIN
STAGING_DOMAIN = 'developer.allizom.org'
STAGING_URL = 'https://' + STAGING_DOMAIN

_PROD_INTERACTIVE_EXAMPLES = 'https://interactive-examples.mdn.mozilla.net'
INTERACTIVE_EXAMPLES_BASE = config(
    'INTERACTIVE_EXAMPLES_BASE', default=_PROD_INTERACTIVE_EXAMPLES)

MAINTENANCE_MODE = config('MAINTENANCE_MODE', default=False, cast=bool)
REVISION_HASH = config('REVISION_HASH', default='undefined')
MANAGERS = ADMINS


# CONN_MAX_AGE: 'persistent' to keep open connection, or max seconds before
# releasing. Default is 0 for a new connection per request.
def parse_conn_max_age(value):
    try:
        return int(value)
    except ValueError:
        assert value.lower() == 'persistent', 'Must be int or "persistent"'
        return None


CONN_MAX_AGE = config('CONN_MAX_AGE', default=60,
                      cast=parse_conn_max_age)
DEFAULT_DATABASE = config('DATABASE_URL',
                          default='mysql://kuma:kuma@localhost:3306/kuma',
                          cast=dj_database_url.parse)


if 'mysql' in DEFAULT_DATABASE['ENGINE']:
    # These are the production settings for OPTIONS.
    DEFAULT_DATABASE.update({
        'CONN_MAX_AGE': CONN_MAX_AGE,
        'OPTIONS': {
            'charset': 'utf8',
            'use_unicode': True,
            'init_command': 'SET '
                            'innodb_strict_mode=1,'
                            'storage_engine=INNODB,'
                            "sql_mode='STRICT_TRANS_TABLES',"
                            'character_set_connection=utf8,'
                            'collation_connection=utf8_general_ci',
        },
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'utf8_general_ci',
        },
    })

DATABASES = {
    'default': DEFAULT_DATABASE,
}


SILENCED_SYSTEM_CHECKS = [
    'django_mysql.W003',
]

# Cache Settings
CACHE_PREFIX = 'kuma'
CACHE_COUNT_TIMEOUT = 60  # in seconds

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'TIMEOUT': CACHE_COUNT_TIMEOUT * 60,
        'KEY_PREFIX': CACHE_PREFIX,
        'LOCATION': config('REDIS_CACHE_SERVER',
                           default='127.0.0.1:6379'),
    }
}

CACHEBACK_CACHE_ALIAS = 'default'

# Email
vars().update(config('EMAIL_URL',
                     default='console://',
                     cast=dj_email_url.parse))
EMAIL_SUBJECT_PREFIX = config('EMAIL_SUBJECT_PREFIX', default='[mdn]')
# Ensure EMAIL_SUBJECT_PREFIX has one trailing space
EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX.strip() + ' '

# Addresses email comes from
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='notifications@developer.mozilla.org'
)
SERVER_EMAIL = config(
    'SERVER_EMAIL',
    default='server-error@developer.mozilla.org'
)

PLATFORM_NAME = platform.node()

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'US/Pacific'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

# Accepted locales.
# The order of some codes is important. For example, 'pt-PT' comes before
# 'pt-BR', so that 'pt-PT' will be selected when the generic 'pt' is requested.
# Candidate locales should be included here and in CANDIDATE_LOCALES
ACCEPTED_LOCALES = (
    'en-US',    # English
    'af',       # Akrikaans
    'ar',       # Arabic
    'az',       # Azerbaijani
    'bg',       # Bulgarian
    'bm',       # Bambara
    'bn-BD',    # Bengali (Bangladesh)
    'bn-IN',    # Bengali (India)
    'ca',       # Catalan
    'cs',       # Czech
    'de',       # German
    'ee',       # Ewe
    'el',       # Greek
    'es',       # Spanish
    'fa',       # Persian
    'ff',       # Fulah
    'fi',       # Finnish
    'fr',       # French
    'fy-NL',    # Frisian (Netherlands)
    'ga-IE',    # Irish (Ireland)
    'ha',       # Hausa
    'he',       # Hebrew
    'hi-IN',    # Hindi (India)
    'hr',       # Croatian *** not in Pontoon
    'hu',       # Hungarian
    'id',       # Indonesian
    'ig',       # Igbo
    'it',       # Italian
    'ja',       # Japanese
    'ka',       # Georgian
    'kab',      # Kabyle
    'ko',       # Korean
    'ln',       # Lingala
    'mg',       # Malagasy
    'ml',       # Malayalam
    'ms',       # Malay
    'my',       # Burmese
    'nl',       # Dutch
    'pl',       # Polish
    'pt-PT',    # Portuguese (Portugal)
    'pt-BR',    # Portuguese (Brazil)
    'ro',       # Romanian
    'ru',       # Russian
    'son',      # Songhay
    'sq',       # Albanian
    'sr',       # Serbian
    'sr-Latn',  # Serbian (Latin)
    'sv-SE',    # Swedish (Sweden)
    'sw',       # Swahili
    'ta',       # Tamil
    'te',       # Telugu
    'th',       # Thai
    'tl',       # Tagalog
    'tn',       # Tswana *** not in Pontoon
    'tr',       # Turkish
    'uk',       # Ukranian
    'vi',       # Vietnamese
    'wo',       # Wolof
    'xh',       # Xhosa
    'yo',       # Yoruba
    'zh-CN',    # Chinese (China)
    'zh-TW',    # Chinese (Taiwan, Province of China)
    'zu',       # Zulu
)

# When there are multiple options for a given language, this gives the
# preferred locale for that language (language => preferred locale).
PREFERRED_LOCALE = {
    'bn': 'bn-BD',
    'pt': 'pt-PT',
    'sr': 'sr',
    'zh': 'zh-CN',
}

# Locales being considered for MDN. This makes the UI strings available for
# localization in Pontoon, but pages can not be translated into this language.
# https://developer.mozilla.org/en-US/docs/MDN/Contribute/Localize/Starting_a_localization
# These should be here and in the ACCEPTED_LOCALES list
CANDIDATE_LOCALES = (
)
# Asserted here to avoid a unit test that is skipped when empty
for candidate in CANDIDATE_LOCALES:
    assert candidate in ACCEPTED_LOCALES

ENABLE_CANDIDATE_LANGUAGES = config('ENABLE_CANDIDATE_LANGUAGES',
                                    default=DEBUG,
                                    cast=bool)

if ENABLE_CANDIDATE_LANGUAGES:
    ENABLED_LOCALES = ACCEPTED_LOCALES[:]
else:
    ENABLED_LOCALES = [locale for locale in ACCEPTED_LOCALES
                       if locale not in CANDIDATE_LOCALES]

RTL_LANGUAGES = (
    'ar',
    'fa',
    'he'
)

# Override generic locale handling with explicit mappings.
# Keys are the requested locale (lowercase); values are the delivered locale.
LOCALE_ALIASES = {
    # Create aliases for over-specific locales.
    'cn': 'zh-CN',

    # Create aliases for locales which use region subtags to assume scripts.
    'zh-hans': 'zh-CN',
    'zh-hant': 'zh-TW',

    # Map locale whose region subtag is separated by `_`(underscore)
    'zh_cn': 'zh-CN',
    'zh_tw': 'zh-TW',
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
    lang_path = path('kuma', 'settings', 'languages.json')
    with open(lang_path, 'r') as lang_file:
        json_locales = json.load(lang_file)

    locales = {}
    for locale, meta in json_locales.items():
        locales[locale] = _Language(meta['English'], meta['native'])
    return locales


LOCALES = _get_locales()
LANGUAGES = [(locale, LOCALES[locale].native) for locale in ENABLED_LOCALES]

# Language list sorted for forms (English, then alphabetical by locale code)
SORTED_LANGUAGES = [LANGUAGES[0]] + sorted(LANGUAGES[1:])

# List of MindTouch locales mapped to Kuma locales.
#
# Language in MindTouch pages are first determined from the locale in the page
# title, with a fallback to the language in the page record.
#
# So, first MindTouch locales were inventoried like so:
#
#     mysql --skip-column-names -uroot wikidb -B \
#           -e 'select page_title from pages  where page_namespace=0' \
#           > page-titles.txt
#
#     grep '/' page-titles.txt | cut -d'/' -f1 | sort -f | uniq -ci | sort -rn
#
# Then, the database languages were inventoried like so:
#
#     select page_language, count(page_id) as ct
#     from pages group by page_language order by ct desc;
#
# Also worth noting, these are locales configured in the prod Control Panel:
#
# en,ar,ca,cs,de,el,es,fa,fi,fr,he,hr,hu,it,ja,
# ka,ko,nl,pl,pt,ro,ru,th,tr,uk,vi,zh-cn,zh-tw
#
# The Kuma side was picked from elements of the MDN_LANGUAGES list in
# settings.py, and a few were added to match MindTouch locales.
#
# Most of these end up being direct mappings, but it's instructive to go
# through the mapping exercise.

MT_TO_KUMA_LOCALE_MAP = {
    'en': 'en-US',
    'ja': 'ja',
    'pl': 'pl',
    'fr': 'fr',
    'es': 'es',
    '': 'en-US',
    'cn': 'zh-CN',
    'zh_cn': 'zh-CN',
    'zh-cn': 'zh-CN',
    'zh_tw': 'zh-TW',
    'zh-tw': 'zh-TW',
    'ko': 'ko',
    'pt': 'pt-PT',
    'de': 'de',
    'it': 'it',
    'ca': 'ca',
    'cs': 'cs',
    'ru': 'ru',
    'nl': 'nl',
    'hu': 'hu',
    'he': 'he',
    'el': 'el',
    'fi': 'fi',
    'tr': 'tr',
    'vi': 'vi',
    'ro': 'ro',
    'ar': 'ar',
    'th': 'th',
    'fa': 'fa',
    'ka': 'ka',
}

LANGUAGE_COOKIE_DOMAIN = DOMAIN
# The number of seconds we are keeping the language preference cookie. (1 year)
LANGUAGE_COOKIE_AGE = 365 * 24 * 60 * 60

SITE_ID = config('SITE_ID', default=1, cast=int)

MDC_PAGES_DIR = path('..', 'mdc_pages')

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = (
    path('locale'),
)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = config('MEDIA_ROOT', default=path('media'))

# Absolute path to the directory for the humans.txt file.
HUMANSTXT_ROOT = MEDIA_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = config('MEDIA_URL', default='/media/')

STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = path('static')

SERVE_MEDIA = False

# Serve diagrams, presentations, and samples from 2005-2012
SERVE_LEGACY = config('SERVE_LEGACY', default=False, cast=bool)
LEGACY_ROOT = config('LEGACY_ROOT', default=None)

# Paths that don't require a locale prefix.
LANGUAGE_URL_IGNORED_PATHS = (
    'healthz',
    'readiness',
    'media',
    'admin',
    'robots.txt',
    'contribute.json',
    'services',
    'static',
    '1',
    'files',
    '@api',
    '__debug__',
    '.well-known',
    'users/github/login/callback/',
    'favicon.ico',
    '_kuma_status.json',
    'humans.txt',
    # Legacy files, circa 2008, served in AWS
    'diagrams',
    'presentations',
    'samples',
    # Legacy files, circa 2008, now return 404
    'patches',
    'web-tech',
    'css',
    'index.php',  # Legacy MediaWiki endpoint, return 404
    # Served in AWS
    'sitemap.xml',
    'sitemaps/',
    'i18n'
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config('SECRET_KEY',
                    default='#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z')


_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.request',
    'django.template.context_processors.csrf',
    'django.contrib.messages.context_processors.messages',

    'kuma.core.context_processors.global_settings',
    'kuma.core.context_processors.i18n',
    'kuma.core.context_processors.next_url',

    'constance.context_processors.config',
)


MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'kuma.core.middleware.RestrictedWhiteNoiseMiddleware',
    # must come before LocaleMiddleware
    'redirect_urls.middleware.RedirectsMiddleware',
    'kuma.core.middleware.SetRemoteAddrFromForwardedFor',
    ('kuma.core.middleware.ForceAnonymousSessionMiddleware'
     if MAINTENANCE_MODE else
     'django.contrib.sessions.middleware.SessionMiddleware'),
    'kuma.core.middleware.LangSelectorMiddleware',
    'kuma.core.middleware.LocaleStandardizerMiddleware',
    # LocaleMiddleware must be before any middleware that uses
    # kuma.core.urlresolvers.reverse() to add locale prefixes to URLs:
    'kuma.core.middleware.LocaleMiddleware',
    'kuma.wiki.middleware.ReadOnlyMiddleware',
    'kuma.core.middleware.Forbidden403Middleware',
    'ratelimit.middleware.RatelimitMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'kuma.core.middleware.SlashMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

if not MAINTENANCE_MODE:
    # We don't want this in maintence mode, as it adds "Cookie"
    # to the Vary header, which in turn, kills caching.
    MIDDLEWARE += ('django.middleware.csrf.CsrfViewMiddleware',)

MIDDLEWARE += (
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'kuma.core.middleware.WaffleWithCookieDomainMiddleware',
    'kuma.core.middleware.RestrictedEndpointsMiddleware',
)

CSP_ENABLE_MIDDLEWARE = config('CSP_ENABLE_MIDDLEWARE',
                               default=False, cast=bool)
if CSP_ENABLE_MIDDLEWARE:
    # For more config, see "Content Security Policy (CSP)" below
    MIDDLEWARE += ('csp.middleware.CSPMiddleware',)


# Auth
AUTHENTICATION_BACKENDS = (
    'kuma.users.auth_backends.KumaAuthBackend',  # Handles User Bans
    'allauth.account.auth_backends.AuthenticationBackend',  # Legacy
)
AUTH_USER_MODEL = 'users.User'
USER_AVATAR_PATH = 'uploads/avatars/'

if urlsplit(STATIC_URL).hostname in (None, 'localhost'):
    # Gravatar needs a publicly available default image
    DEFAULT_AVATAR = PRODUCTION_URL + '/static/img/avatar.png'
else:
    DEFAULT_AVATAR = STATIC_URL + 'img/avatar.png'

AVATAR_SIZES = [  # in pixels
    34,   # wiki document page
    48,   # user_link helper
    200,  # user pages
    220,  # default, e.g. used in feeds
]
ACCOUNT_ACTIVATION_DAYS = 30
MAX_AVATAR_FILE_SIZE = 131072  # 100k, in bytes

ROOT_URLCONF = 'kuma.urls'

CKEDITOR_DEV = config('CKEDITOR_DEV', default=False, cast=bool)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.CachedFileFinder',
    'pipeline.finders.PipelineFinder',
)

STATICFILES_STORAGE = ('pipeline.storage.NonPackagingPipelineStorage'
                       if DEBUG else
                       'kuma.core.pipeline.storage.ManifestPipelineStorage')

STATICFILES_DIRS = [
    path('assets', 'static'),
    path('kuma', 'static'),
    path('kuma', 'javascript', 'dist'),
    path('build', 'locale'),
    path('jinja2', 'includes/icons'),
    ('js/libs/ckeditor4/build', path('assets', 'ckeditor4', 'build')),
]
if CKEDITOR_DEV:
    STATICFILES_DIRS.append(('js/libs/ckeditor4/source',
                             path('assets', 'ckeditor4', 'source')))

# TODO: Figure out why changing the order of apps (for example, moving taggit
# higher in the list) breaks tests.
INSTALLED_APPS = (
    # django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'flat',
    'django.contrib.admin',

    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'soapbox',  # must be before kuma.wiki, or RemovedInDjango19Warning

    # MDN
    'kuma.payments.apps.PaymentsConfig',
    'kuma.core.apps.CoreConfig',
    'kuma.banners',
    'kuma.feeder.apps.FeederConfig',
    'kuma.landing',
    'kuma.redirects',
    'kuma.scrape',
    'kuma.search.apps.SearchConfig',
    'kuma.users.apps.UserConfig',
    'kuma.wiki.apps.WikiConfig',
    'kuma.api.apps.APIConfig',
    'kuma.attachments.apps.AttachmentsConfig',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'kuma.users.providers.github',

    # util
    'django_jinja',
    'pipeline',
    'puente',
    'constance.backends.database',
    'constance',
    'waffle',
    'kuma.authkeys',
    'tidings',
    'taggit',
    'honeypot',
    'cacheback',
    'django_extensions',
    'captcha',

    'kuma.dashboards',
    'statici18n',
    'rest_framework',
    'django_mysql',

    # other
    'kuma.humans.apps.HumansConfig',
    'redirect_urls',
)

# Feed fetcher config
FEEDER_TIMEOUT = 6  # in seconds

TEMPLATES = [
    {
        'NAME': 'jinja2',
        'BACKEND': 'django_jinja.backend.Jinja2',
        'DIRS': [path('jinja2'), path('static')],
        'APP_DIRS': True,
        'OPTIONS': {
            # Use jinja2/ for jinja templates
            'app_dirname': 'jinja2',
            # Don't figure out which template loader to use based on
            # file extension
            'match_extension': '',
            'newstyle_gettext': True,
            'context_processors': _CONTEXT_PROCESSORS,
            'undefined': 'jinja2.Undefined',
            'extensions': [
                'jinja2.ext.do',
                'jinja2.ext.loopcontrols',
                'jinja2.ext.i18n',
                'puente.ext.i18n',
                'django_jinja.builtins.extensions.CsrfExtension',
                'django_jinja.builtins.extensions.CacheExtension',
                'django_jinja.builtins.extensions.TimezoneExtension',
                'django_jinja.builtins.extensions.UrlsExtension',
                'django_jinja.builtins.extensions.StaticFilesExtension',
                'django_jinja.builtins.extensions.DjangoFiltersExtension',
                'pipeline.jinja2.PipelineExtension',
                'waffle.jinja.WaffleExtension',
                'kuma.core.i18n.TranslationExtension',
            ],
        }
    },
    {
        'NAME': 'django',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [path('templates')],
        'APP_DIRS': False,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': _CONTEXT_PROCESSORS,
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        }
    },
]

PUENTE = {
    'VERSION': '2019.15',
    'BASE_DIR': BASE_DIR,
    'TEXT_DOMAIN': 'django',
    # Tells the extract script what files to look for l10n in and what function
    # handles the extraction.
    'DOMAIN_METHODS': {
        'django': [
            ('kumascript/node_modules/**', 'ignore'),
            ('kuma/**.py', 'python'),
            ('**/templates/**.html', 'django_babel.extract.extract_django'),
            ('**/jinja2/**.html', 'jinja2'),
            ('**/jinja2/**.ltxt', 'jinja2'),
        ],
        'javascript': [
            # We can't say **.js because that would dive into any libraries.
            ('kuma/static/js/*.js', 'javascript'),
            ('kuma/static/js/components/**.js', 'javascript'),
            ('assets/ckeditor4/source/plugins/mdn-**/*.js',
             'javascript'),
        ],
        'react': [
            ('kuma/javascript/src/**.js', 'javascript'),
            ('kuma/javascript/src/**.jsx', 'javascript'),
        ],
    },
    'PROJECT': 'MDN',
    'MSGID_BUGS_ADDRESS': ADMIN_EMAILS[0],
}

# Combine JavaScript strings into React domain
PUENTE['DOMAIN_METHODS']['react'] = (
    PUENTE['DOMAIN_METHODS']['javascript'] +
    PUENTE['DOMAIN_METHODS']['react'])

STATICI18N_ROOT = 'build/locale'
STATICI18N_DOMAIN = 'javascript'

# Cache non-versioned static files for one week
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 7


def pipeline_scss(output, sources, **kwargs):
    """Define a CSS file generated from multiple SCSS files."""
    definition = {
        'source_filenames': tuple('styles/%s.scss' % src for src in sources),
        'output_filename': 'build/styles/%s.css' % output
    }
    definition.update(kwargs)
    return definition


def pipeline_one_scss(slug, **kwargs):
    """Define a CSS file that shares the name with the one input SCSS."""
    return pipeline_scss(slug, [slug], **kwargs)


PIPELINE_CSS = {
    # Combines the mdn, wiki and wiki-compat-tables styles into
    # one bundle for use by pages that are part of the new
    # single page app.
    'react-mdn': {
        'source_filenames': (
            'styles/main-shared.scss',
            'styles/wiki-shared.scss',

            # Custom build of our Prism theme
            'styles/libs/prism/prism.css',
            'styles/libs/prism/prism-line-highlight.css',
            'styles/libs/prism/prism-line-numbers.css',

            'js/prism-mdn/components/prism-json.css',
            'styles/wiki-syntax.scss',

            # Styles for BCD tables
            'styles/wiki-compat-tables.scss',

            # Styles for call-to-action banners
            # See kuma/javascript/src/banners.jsx
            'styles/components/banners/base.scss'
        ),
        'output_filename': 'build/styles/react-mdn.css',
    },

    'mdn': {
        'source_filenames': (
            'styles/main.scss',
        ),
        'output_filename': 'build/styles/mdn.css',
    },
    'banners': {
        'source_filenames': (
            'styles/components/banners/base.scss',
        ),
        'output_filename': 'build/styles/banners.css',
    },
    'jquery-ui': {
        'source_filenames': (
            'js/libs/jquery-ui-1.10.3.custom/css/ui-lightness/jquery-ui-1.10.3.custom.min.css',
            'styles/libs/jqueryui/moz-jquery-plugins.css',
            'css/jquery-ui-customizations.scss',
        ),
        'output_filename': 'build/styles/jquery-ui.css',
    },
    'home': {
        'source_filenames': (
            'styles/home.scss',
        ),
        'output_filename': 'build/styles/home.css',
    },
    'search': {
        'source_filenames': (
            'styles/search.scss',
        ),
        'output_filename': 'build/styles/search.css',
    },
    'wiki': {
        'source_filenames': (
            'styles/components/banners/wiki-notice.scss',
            'styles/wiki.scss',
            'styles/diff.scss',

            # Custom build of our Prism theme
            'styles/libs/prism/prism.css',
            'styles/libs/prism/prism-line-highlight.css',
            'styles/libs/prism/prism-line-numbers.css',

            'js/prism-mdn/components/prism-json.css',
            'styles/wiki-syntax.scss',
        ),
        'output_filename': 'build/styles/wiki.css',
    },
    'wiki-revisions': {
        'source_filenames': (
            'styles/wiki-revisions.scss',
        ),
        'output_filename': 'build/styles/wiki-revisions.css',
    },
    'wiki-edit': {
        'source_filenames': (
            'styles/wiki-edit.scss',
        ),
        'output_filename': 'build/styles/wiki-edit.css',
    },
    'wiki-compat-tables': {
        'source_filenames': (
            'styles/wiki-compat-tables.scss',
        ),
        'output_filename': 'build/styles/wiki-compat-tables.css',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    'users': {
        'source_filenames': (
            'styles/users.scss',
        ),
        'output_filename': 'build/styles/users.css',
    },
    'tagit': {
        'source_filenames': (
            'styles/libs/jquery.tagit.css',
        ),
        'output_filename': 'build/styles/tagit.css',
    },
    'promote': {
        'source_filenames': (
            'styles/promote.scss',
        ),
        'output_filename': 'build/styles/promote.css',
    },
    'error': {
        'source_filenames': (
            'styles/error.scss',
        ),
        'output_filename': 'build/styles/error.css',
    },
    'error-404': {
        'source_filenames': (
            'styles/error.scss',
            'styles/error-404.scss',
        ),
        'output_filename': 'build/styles/error-404.css',
    },
    'dashboards': {
        'source_filenames': (
            'styles/dashboards.scss',
            'styles/diff.scss',
        ),
        'output_filename': 'build/styles/dashboards.css',
    },
    'submission': {
        'source_filenames': (
            'styles/submission.scss',
        ),
        'output_filename': 'build/styles/submission.css',
    },
    'user-banned': {
        'source_filenames': (
            'styles/user-banned.scss',
        ),
        'output_filename': 'build/styles/user-banned.css',
    },
    'error-403-alternate': {
        'source_filenames': (
            'styles/error-403-alternate.scss',
        ),
        'output_filename': 'build/styles/error-403-alternate.css',
    },
    'editor-content': {
        'source_filenames': (
            'styles/main.scss',
            'styles/wiki.scss',
            'styles/wiki-wysiwyg.scss',
            'styles/wiki.scss',
        ),
        'output_filename': 'build/styles/editor-content.css',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    # for maintenance mode page
    'maintenance-mode': {
        'source_filenames': (
            'styles/maintenance-mode.scss',
        ),
        'output_filename': 'build/styles/maintenance-mode.css',
    },
    # global maintenance-mode-styles
    'maintenance-mode-global': {
        'source_filenames': (
            'styles/maintenance-mode-global.scss',
        ),
        'output_filename': 'build/styles/maintenance-mode-global.css',
    },
    # embeded iframe for live samples
    'samples': {
        'source_filenames': (
            'styles/samples.scss',
        ),
        'output_filename': 'build/styles/samples.css',
    },
}

# Locales that are well supported by the Zilla family
LOCALE_USE_ZILLA = [
    'ca',
    'cs',
    'de',
    'ee',
    'en-US',
    'es',
    'fi',
    'fr',
    'fy-NL',
    'ga-IE',
    'ha',
    'hr',
    'hu',
    'id',
    'ig',
    'it',
    'kab',
    'ln',
    'mg',
    'ms',
    'nl',
    'pl',
    'pt-BR',
    'pt-PT',
    'sq',
    'sv-SE',
    'sw',
    'tl',
]


PIPELINE_JS = {
    'main': {
        'source_filenames': (
            'js/libs/jquery/jquery.js',
            'js/libs/jquery-ajax-prefilter.js',
            'js/libs/icons.js',
            'js/components.js',
            'js/analytics.js',
            'js/main.js',
            'js/components/nav-main-search.js',
            'js/auth.js',
            'js/highlight.js',
            'js/wiki-compat-trigger.js',
            'js/lang-switcher.js',
        ),
        'output_filename': 'build/js/main.js',
    },
    'react-main': {
        'source_filenames': (
            # TODO: these are the last legacy files from the wiki site
            # that we're still using on the React-based pages. Ideally
            # we should just move these to the React code so webpack
            # can deal with them.
            'js/utils/post-message-handler.js',
            'js/analytics.js',

            # Custom Prism build
            # TODO: the prism.js file should be imported dynamcally
            # when we need it instead of being hardcoded in here.
            "js/libs/prism/prism-core.js",
            "js/libs/prism/prism-bash.js",
            "js/libs/prism/prism-markup.js",
            "js/libs/prism/prism-css.js",
            "js/libs/prism/prism-clike.js",
            "js/libs/prism/prism-javascript.js",
            "js/libs/prism/prism-json.js",
            "js/libs/prism/prism-jsonp.js",
            "js/libs/prism/prism-css-extras.js",
            "js/libs/prism/prism-rust.js",
            "js/libs/prism/prism-wasm.js",
            "js/libs/prism/prism-line-highlight.js",
            "js/libs/prism/prism-line-numbers.js",

            # The react.js file is created by webpack and
            # placed in the kuma/javascript/dist/ directory.
            'react.js'
        ),
        'output_filename': 'build/js/react-main.js',
    },
    'bcd-signal': {
        'source_filenames': (
            'bcd-signal.js',
        ),
        'output_filename': 'build/js/react-bcd-signal.js',
        'extra_context': {
            'defer': True,
        },
    },
    'banners': {
        'source_filenames': (
            'js/components/banners/utils/banners-event-util.js',
            'js/components/banners/utils/banners-state-util.js',
            'js/components/banners/banners.js',
        ),
        'output_filename': 'build/js/banners.js',
        'extra_context': {
            'async': True,
        },
    },
    'users': {
        'source_filenames': (
            'js/libs/tag-it.js',
            'js/moz-jquery-plugins.js',
            'js/users.js',
        ),
        'output_filename': 'build/js/users.js',
        'extra_context': {
            'async': True,
        },
    },
    'dashboard': {
        'source_filenames': (
            'js/dashboard.js',
        ),
        'output_filename': 'build/js/dashboard.js',
        'extra_context': {
            'async': True,
        },
    },
    'jquery-ui': {
        'source_filenames': (
            'js/libs/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js',
            'js/libs/jquery-ajax-prefilter.js',
            'js/moz-jquery-plugins.js',
        ),
        'output_filename': 'build/js/jquery-ui.js',
    },
    'search': {
        'source_filenames': (
            'js/search.js',
        ),
        'output_filename': 'build/js/search.js',
        'extra_context': {
            'async': True,
        },
    },
    'payments': {
        'source_filenames': (
            'js/components/payments/payments-manage.js',
        ),
        'output_filename': 'build/js/payments.js',
    },
    'framebuster': {
        'source_filenames': (
            'js/framebuster.js',
        ),
        'output_filename': 'build/js/framebuster.js',
    },
    'syntax-prism': {
        'source_filenames': (
            # Custom Prism build
            "js/libs/prism/prism-core.js",
            "js/libs/prism/prism-bash.js",
            "js/libs/prism/prism-markup.js",
            "js/libs/prism/prism-css.js",
            "js/libs/prism/prism-clike.js",
            "js/libs/prism/prism-javascript.js",
            "js/libs/prism/prism-json.js",
            "js/libs/prism/prism-jsonp.js",
            "js/libs/prism/prism-css-extras.js",
            "js/libs/prism/prism-rust.js",
            "js/libs/prism/prism-wasm.js",
            "js/libs/prism/prism-line-highlight.js",
            "js/libs/prism/prism-line-numbers.js",

            'js/syntax-prism.js',
        ),
        'output_filename': 'build/js/syntax-prism.js',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    'wiki': {
        'source_filenames': (
            'js/utils/utils.js',
            'js/utils/post-message-handler.js',
            'js/wiki.js',
            'js/utils/bug1522937-iex-test.js',
            'js/interactive.js',
            'js/wiki-samples.js',
            'js/wiki-toc.js',
            'js/components/local-anchor.js',
            'js/components/page-load-actions.js',
        ),
        'output_filename': 'build/js/wiki.js',
        'extra_context': {
            'async': True,
        },
    },
    'wiki-edit': {
        'source_filenames': (
            'js/wiki-edit.js',
            'js/wiki-edit-draft.js',
            'js/libs/tag-it.js',
            'js/wiki-tags-edit.js',
        ),
        'output_filename': 'build/js/wiki-edit.js',
    },
    'wiki-move': {
        'source_filenames': (
            'js/wiki-move.js',
        ),
        'output_filename': 'build/js/wiki-move.js',
        'extra_context': {
            'async': True,
        },
    },
    'wiki-compat-tables': {
        'source_filenames': (
            'js/wiki-compat-tables.js',
        ),
        'output_filename': 'build/js/wiki-compat-tables.js',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    'wiki-compat-signal': {
        'source_filenames': (
            'js/wiki-compat-signal.js',
        ),
        'output_filename': 'build/js/wiki-compat-signal.js',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    'task-completion': {
        'source_filenames': (
            'js/task-completion.js',
        ),
        'output_filename': 'build/js/task-completion.js',
        'extra_context': {
            'async': True,
        },
    },
    'newsletter': {
        'source_filenames': (
            'js/newsletter.js',
        ),
        'output_filename': 'build/js/newsletter.js',
        'extra_context': {
            'async': True,
        },
    },
    'html5shiv': {
        'source_filenames': (
            'js/libs/html5shiv/html5shiv.js',
        ),
        'output_filename': 'build/js/html5shiv.js',
    },
    'selectivizr': {
        'source_filenames': (
            'js/libs/selectivizr/selectivizr.js',
        ),
        'output_filename': 'build/js/selectivizr.js',
    },
    'perf': {
        'source_filenames': (
            'js/utils/perf.js',
            'js/utils/perf-post-message-handler.js',
        ),
        'output_filename': 'build/js/perf.js',
        'extra_context': {
            'async': True,
        },
    },
}

PIPELINE = {
    'STYLESHEETS': PIPELINE_CSS,
    'JAVASCRIPT': PIPELINE_JS,
    'DISABLE_WRAPPER': True,
    'SHOW_ERRORS_INLINE': False,  # django-pipeline issue #614
    'COMPILERS': (
        ('kuma.core.pipeline.sass.DebugSassCompiler'
            if DEBUG else
            'pipeline.compilers.sass.SASSCompiler'),
    ),
    'SASS_BINARY': config('PIPELINE_SASS_BINARY',
                          default='/usr/bin/env node-sass'),
    'SASS_ARGUMENTS': config('PIPELINE_SASS_ARGUMENTS', default=''),
    'CSS_COMPRESSOR': config('PIPELINE_CSS_COMPRESSOR',
                             default='kuma.core.pipeline.cleancss.CleanCSSCompressor'),
    'JS_COMPRESSOR': config('PIPELINE_JS_COMPRESSOR',
                            default='pipeline.compressors.uglifyjs.UglifyJSCompressor'),
    'PIPELINE_ENABLED': config('PIPELINE_ENABLED', not DEBUG, cast=bool),
    'PIPELINE_COLLECTOR_ENABLED': config('PIPELINE_COLLECTOR_ENABLED', not DEBUG, cast=bool),
}
# Pipeline compressor overrides
# For example, PIPELINE_YUGLIFY_BINARY will set YUGLIFY_BINARY
# https://django-pipeline.readthedocs.io/en/latest/compressors.html
pipeline_overrides = (
    'YUGLIFY_BINARY',
    'YUGLIFY_CSS_ARGUMENTS'
    'YUGLIFY_JS_ARGUMENTS',
    'YUI_BINARY',
    'YUI_CSS_ARGUMENTS',
    'YUI_JS_ARGUMENTS',
    'CLOSURE_BINARY',
    'CLOSURE_ARGUMENTS',
    'UGLIFYJS_BINARY',
    'UGLIFYJS_ARGUMENTS',
    'CSSTIDY_BINARY',
    'CSSTIDY_ARGUMENTS',
    'CSSMIN_BINARY',
    'CSSMIN_ARGUMENTS',
    'CLEANCSS_BINARY',
    'CLEANCSS_ARGUMENTS',
)
for override in pipeline_overrides:
    env_value = config('PIPELINE_' + override, default=None)
    if env_value is not None:
        PIPELINE[override] = env_value

# Session cookies
SESSION_COOKIE_DOMAIN = DOMAIN
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = config(
    'SESSION_COOKIE_AGE',
    default=60 * 60 * 24 * 365,
    cast=int
)

WAFFLE_SECURE = config('WAFFLE_COOKIE_SECURE', default=True, cast=bool)
# This is a setting unique to Kuma which specifies the domain
# that will be used for all of the waffle cookies. It is used by
# kuma.core.middleware.WaffleWithCookieDomainMiddleware.
WAFFLE_COOKIE_DOMAIN = DOMAIN

# bug 856061
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='developer-local.allizom.org, mdn-local.mozillademos.org',
    cast=Csv()
)

# Maximum length of the filename. Forms should use this and raise
# ValidationError if the length is exceeded.
# @see http://code.djangoproject.com/ticket/9893
# Columns are 250 but this leaves 50 chars for the upload_to prefix
MAX_FILENAME_LENGTH = 200
MAX_FILEPATH_LENGTH = 250

_PROD_ATTACHMENT_HOST = 'mdn.mozillademos.org'
_PROD_ATTACHMENT_SITE_URL = 'https://' + _PROD_ATTACHMENT_HOST
ATTACHMENT_HOST = config('ATTACHMENT_HOST', default=_PROD_ATTACHMENT_HOST)
ATTACHMENT_SITE_URL = PROTOCOL + ATTACHMENT_HOST
_PROD_ATTACHMENT_ORIGIN = 'demos-origin.mdn.mozit.cloud'
ATTACHMENT_ORIGIN = config('ATTACHMENT_ORIGIN', default=_PROD_ATTACHMENT_ORIGIN)

BETA_HOST = config('BETA_HOST', default='beta.' + DOMAIN)
BETA_ORIGIN = config('BETA_ORIGIN', default='beta.mdn.mozit.cloud')
BETA_SITE_URL = PROTOCOL + BETA_HOST
WIKI_HOST = config('WIKI_HOST', default='wiki.' + DOMAIN)
WIKI_SITE_URL = PROTOCOL + WIKI_HOST

# This should never be false for the production and stage deployments.
ENABLE_RESTRICTIONS_BY_HOST = config(
    'ENABLE_RESTRICTIONS_BY_HOST',
    default=True,
    cast=bool
)

# Allow robots, but restrict some paths
# If the domain is a CDN, the CDN origin should be included.
ALLOW_ROBOTS_WEB_DOMAINS = set(
    config('ALLOW_ROBOTS_WEB_DOMAINS',
           default='developer.mozilla.org',
           cast=Csv()))

# Allow robots, no path restrictions
# If the domain is a CDN, the CDN origin should be included.
ALLOW_ROBOTS_DOMAINS = set(
    config('ALLOW_ROBOTS_DOMAINS',
           default=','.join((_PROD_ATTACHMENT_HOST, _PROD_ATTACHMENT_ORIGIN)),
           cast=Csv()))


# Allowed iframe URL patterns
# The format is a three-element tuple:
#  Protocol: Required, must match
#  Domain: Required, must match
#  Path: An optional path prefix or matching regex

def parse_iframe_url(url):
    '''
    Parse an iframe URL into an allowed iframe pattern

    A URL with a '*' in the path is treated as a regex.
    '''
    parts = urlsplit(url)
    assert parts.scheme in ('http', 'https')
    path = ''
    if parts.path.strip('/') != '':
        if '*' in parts.path:
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
    parse_iframe_url('https://mdn.github.io/'),
    # Videos, https://developer.mozilla.org/en-US/docs/Tools/Web_Console
    parse_iframe_url('https://www.youtube.com/embed/'),
    # Samples, https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures
    parse_iframe_url('https://jsfiddle.net/.*/embedded/.*'),
    # Charts, https://developer.mozilla.org/en-US/docs/MDN/Kuma/Server_charts
    parse_iframe_url('https://rpm.newrelic.com/public/charts/'),
]

# Add the overridden attachment / live sample host
if ATTACHMENT_SITE_URL != _PROD_ATTACHMENT_SITE_URL:
    ALLOWED_IFRAME_PATTERNS.append(parse_iframe_url(ATTACHMENT_SITE_URL))

# Add the overridden interactive examples service
if INTERACTIVE_EXAMPLES_BASE != _PROD_INTERACTIVE_EXAMPLES:
    ALLOWED_IFRAME_PATTERNS.append(parse_iframe_url(INTERACTIVE_EXAMPLES_BASE))

# Add more iframe patterns from the environment
_ALLOWED_IFRAME_PATTERNS = config('ALLOWED_IFRAME_PATTERNS', default='', cast=Csv())
for pattern in _ALLOWED_IFRAME_PATTERNS:
    ALLOWED_IFRAME_PATTERNS.append(parse_iframe_url(pattern))

# Allow all iframe sources (for debugging)
ALLOW_ALL_IFRAMES = config('ALLOW_ALL_IFRAMES', default=False, cast=bool)


# Video settings, hard coded here for now.
# TODO: figure out a way that doesn't need these values
WIKI_VIDEO_WIDTH = 640
WIKI_VIDEO_HEIGHT = 480

IMAGE_MAX_FILESIZE = 1048576  # 1 megabyte, in bytes
THUMBNAIL_SIZE = 120  # Thumbnail size, in pixels
THUMBNAIL_UPLOAD_PATH = 'uploads/images/thumbnails/'
IMAGE_UPLOAD_PATH = 'uploads/images/'
# A string listing image mime types to accept, comma separated.
# String must not contain double quotes!
IMAGE_ALLOWED_MIMETYPES = 'image/jpeg,image/png,image/gif'

# Email
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.filebased.EmailBackend'
)
EMAIL_FILE_PATH = '/app/tmp/emails'

# Content Security Policy (CSP)
CSP_DEFAULT_SRC = ("'none'",)
CSP_CONNECT_SRC = [
    SITE_URL,
    BETA_SITE_URL,
    WIKI_SITE_URL,
]
CSP_FONT_SRC = [
    SITE_URL,
]
CSP_FRAME_SRC = [
    urlunsplit((scheme, netloc, '', '', ''))
    for scheme, netloc, ignored_path in ALLOWED_IFRAME_PATTERNS]

CSP_IMG_SRC = [
    SITE_URL,
    BETA_SITE_URL,
    "data:",
    PROTOCOL + "i2.wp.com",
    "https://secure.gravatar.com",
    "https://www.google-analytics.com",
    _PROD_ATTACHMENT_SITE_URL,
    WIKI_SITE_URL,
]
if ATTACHMENT_SITE_URL not in (_PROD_ATTACHMENT_SITE_URL, SITE_URL):
    CSP_IMG_SRC.append(ATTACHMENT_SITE_URL)

CSP_SCRIPT_SRC = [
    SITE_URL,
    "www.google-analytics.com",
    "cdn.speedcurve.com",
    "static.codepen.io",
    # TODO fix things so that we don't need this
    "'unsafe-inline'",
    WIKI_SITE_URL,
]
CSP_STYLE_SRC = [
    SITE_URL,
    # TODO fix things so that we don't need this
    "'unsafe-inline'",
    WIKI_SITE_URL,
]
CSP_REPORT_ONLY = config('CSP_REPORT_ONLY', default=False, cast=bool)
CSP_REPORT_ENABLE = config('CSP_REPORT_ENABLE', default=False, cast=bool)
SENTRY_ENVIRONMENT = config('SENTRY_ENVIRONMENT', default=None)
if CSP_REPORT_ENABLE:
    CSP_REPORT_URI = config('CSP_REPORT_URI', default='/csp-violation-capture')
    if "sentry_key=" in CSP_REPORT_URI:
        # Using sentry to report. Optionally add revision and environment
        bits = urlsplit(CSP_REPORT_URI)
        query = parse_qs(bits.query)
        if REVISION_HASH and REVISION_HASH != 'undefined':
            query['sentry_release'] = REVISION_HASH
        if SENTRY_ENVIRONMENT:
            query['sentry_environment'] = SENTRY_ENVIRONMENT
        CSP_REPORT_URI = urlunsplit((bits.scheme, bits.netloc, bits.path,
                                     urlencode(query, doseq=True),
                                     bits.fragment))

# Celery (asynchronous tasks)
CELERY_BROKER_URL = config('CELERY_BROKER_URL',
                           default='redis://0.0.0.0:6379/0')

CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', False, cast=bool)
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_WORKER_CONCURRENCY = config('CELERY_WORKER_CONCURRENCY', default=4, cast=int)

# Maximum tasks run before auto-restart of child process,
# to mitigate memory leaks. None / 0 means unlimited tasks
CELERY_WORKER_MAX_TASKS_PER_CHILD = config(
    'CELERY_WORKER_MAX_TASKS_PER_CHILD',
    default=0,
    cast=int
) or None


# Sadly, kuma depends on pickle being the default serializer.
# In Celery 4, the default is now JSON.
# It's probably too late to switch all tasks to work with either.
# Just remember, avoid passing types that are non-trivial and is
# different in pickle vs json. Keep things simple. Even if it means
# you have to do type conversions in the tasks' code.
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_EVENT_SERIALIZER = 'pickle'


CELERY_IMPORTS = (
    'kuma.search.tasks',
    'tidings.events',
)

CELERY_TASK_ANNOTATIONS = {
    'cacheback.tasks.refresh_cache': {
        'rate_limit': '120/m',
    }
}

CELERY_TASK_ROUTES = {
    'cacheback.tasks.refresh_cache': {
        'queue': 'mdn_purgeable'
    },
    'kuma.core.tasks.clean_sessions': {
        'queue': 'mdn_purgeable'
    },
    'kuma.core.tasks.delete_old_ip_bans': {
        'queue': 'mdn_purgeable'
    },
    'kuma.humans.tasks.humans_txt': {
        'queue': 'mdn_purgeable'
    },
    'kuma.wiki.tasks.build_index_sitemap': {
        'queue': 'mdn_purgeable'
    },
    'kuma.wiki.tasks.build_locale_sitemap': {
        'queue': 'mdn_purgeable'
    },
    'kuma.wiki.tasks.build_sitemaps': {
        'queue': 'mdn_purgeable'
    },
    'kuma.wiki.tasks.delete_old_revision_ips': {
        'queue': 'mdn_purgeable'
    },
    'kuma.wiki.tasks.tidy_revision_content': {
        'queue': 'mdn_purgeable'
    },
    'kuma.search.tasks.prepare_index': {
        'queue': 'mdn_search'
    },
    'kuma.search.tasks.finalize_index': {
        'queue': 'mdn_search'
    },
    'kuma.wiki.tasks.index_documents': {
        'queue': 'mdn_search'
    },
    'kuma.wiki.tasks.unindex_documents': {
        'queue': 'mdn_search'
    },
    'kuma.users.tasks.send_welcome_email': {
        'queue': 'mdn_emails'
    },
    'kuma.users.tasks.email_document_progress': {
        'queue': 'mdn_emails'
    },
    'kuma.wiki.tasks.send_first_edit_email': {
        'queue': 'mdn_emails'
    },
    'tidings.events._fire_task': {
        'queue': 'mdn_emails'
    },
    'tidings.events.claim_watches': {
        'queue': 'mdn_emails'
    },
    'kuma.wiki.tasks.move_page': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.acquire_render_lock': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.release_render_lock': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.render_document': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.render_document_chunk': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.clean_document_chunk': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.render_stale_documents': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.build_json_data_for_document': {
        'queue': 'mdn_wiki'
    },
    'kuma.feeder.tasks.update_feeds': {
        'queue': 'mdn_purgeable'
    },
    'kuma.api.tasks.publish': {
        'queue': 'mdn_api'
    },
    'kuma.api.tasks.unpublish': {
        'queue': 'mdn_api'
    },
    'kuma.api.tasks.request_cdn_cache_invalidation': {
        'queue': 'mdn_api'
    },
}

# Wiki rebuild settings
WIKI_REBUILD_TOKEN = 'kuma:wiki:full-rebuild'
WIKI_REBUILD_ON_DEMAND = False

# Top contributors cache settings
TOP_CONTRIBUTORS_CACHE_KEY = 'kuma:TopContributors'
TOP_CONTRIBUTORS_CACHE_TIMEOUT = 60 * 60 * 12

# Do not change this without also deleting all wiki documents:
WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE

TIDINGS_FROM_ADDRESS = 'notifications@developer.mozilla.org'
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = True

CONSTANCE_BACKEND = ('kuma.core.backends.ReadOnlyConstanceDatabaseBackend'
                     if MAINTENANCE_MODE else
                     'constance.backends.database.DatabaseBackend')
# must be an entry in the CACHES setting!
CONSTANCE_DATABASE_CACHE_BACKEND = 'default'

# Settings and defaults controllable by Constance in admin
CONSTANCE_CONFIG = dict(
    BETA_GROUP_NAME=(
        'Beta Testers',
        'Name of the django.contrib.auth.models.Group to use as beta testers'
    ),
    KUMA_DOCUMENT_RENDER_TIMEOUT=(
        180.0,
        'Maximum seconds to wait before considering a rendering in progress or '
        'scheduled as failed and allowing another attempt.'
    ),
    KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT=(
        10.0,
        'Maximum seconds to allow a document to spend rendering during the '
        'response cycle before flagging it to be sent to the deferred rendering '
        'queue for future renders.'
    ),
    KUMASCRIPT_TIMEOUT=(
        0.0,
        'Maximum seconds to wait for a response from the kumascript service. '
        'On timeout, the document gets served up as-is and without macro '
        'evaluation as an attempt at graceful failure. NOTE: a value of 0 '
        'disables kumascript altogether.'
    ),
    KUMASCRIPT_MAX_AGE=(
        600,
        'Maximum acceptable age (in seconds) of a cached response from '
        'kumascript. Passed along in a Cache-Control: max-age={value} header, '
        'which tells kumascript whether or not to serve up a cached response.'
    ),
    DIFF_CONTEXT_LINES=(
        0,
        'Number of lines of context to show in diff display.',
    ),
    FEED_DIFF_CONTEXT_LINES=(
        3,
        'Number of lines of context to show in feed diff display.',
    ),
    WIKI_ATTACHMENT_ALLOWED_TYPES=(
        'image/gif image/jpeg image/png image/svg+xml text/html image/vnd.adobe.photoshop',
        'Allowed file types for wiki file attachments',
    ),
    WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS=(
        14,
        "Number of days to keep the trashed attachments files before they "
        "are removed from the file storage"
    ),
    KUMA_WIKI_IFRAME_ALLOWED_HOSTS=(
        (r'^https?\:\/\/'
         r'(stage-files.mdn.moz.works'              # Staging demos
         r'|mdn.mozillademos.org'                   # Production demos
         r'|testserver'                             # Unit test demos
         r'|localhost\:8000'                        # Docker development demos
         r'|localhost\:8080'                        # Embedded samples server
         r'|rpm.newrelic.com\/public\/charts\/.*'   # MDN/Kuma/Server_charts
         r'|(www.)?youtube.com\/embed\/(\.*)'       # Embedded videos
         r'|jsfiddle.net\/.*embedded.*'             # Embedded samples
         r'|mdn.github.io'                          # Embedded samples
         r'|interactive-examples.mdn.mozilla.net'   # Embedded samples
         r')'),
        'Regex comprised of domain names that are allowed for IFRAME SRCs'
    ),
    # TODO: Delete this line once we know that the production environment
    # definitely has 'GOOGLE_ANALYTICS_ACCOUNT' set.
    # See https://bugzilla.mozilla.org/show_bug.cgi?id=1570076
    GOOGLE_ANALYTICS_ACCOUNT=(
        '0',
        '(This is deprecated and will disappear)',
    ),
    GOOGLE_ANALYTICS_CREDENTIALS=(
        '{}',
        'Google Analytics (read-only) API credentials',
    ),
    WIKI_DOCUMENT_TAG_SUGGESTIONS=(
        json.dumps([
            "Accessibility", "AJAX", "API", "Apps", "B2G OS",
            "Canvas", "CSS", "Device", "DOM", "Events",
            "Extensions", "Firefox", "Firefox OS", "Games",
            "Gecko", "Graphics", "Internationalization", "History", "HTML", "HTTP", "JavaScript", "Layout",
            "Localization", "MDN", "Mobile", "Mozilla",
            "Networking", "Persona", "Places", "Plugins", "Protocols",

            "Reference", "Tutorial", "Landing",

            "junk", "NeedsMarkupWork", "NeedsContent", "NeedsExample",
        ]),
        "JSON array listing tag suggestions for documents"
    ),
    COMMON_REASONS_TO_BAN_USERS=(
        json.dumps([
            'Spam', 'Profile Spam ', 'Sandboxing', 'Incorrect Translation', 'Penetration Testing',
        ]),
        "JSON array listing some common reasons to ban users",
    ),
    SESSION_CLEANUP_CHUNK_SIZE=(
        1000,
        'Number of expired sessions to cleanup up in one go.',
    ),
    WELCOME_EMAIL_FROM=(
        "Janet Swisher <no-reply@mozilla.org>",
        'Email address from which welcome emails will be sent',
    ),
    EMAIL_LIST_SPAM_WATCH=(
        "mdn-spam-watch@mozilla.com",
        "Email address to notify of possible spam (first edits, blocked edits)",
    ),
    AKISMET_KEY=(
        '',
        'API key for Akismet spam checks, leave empty to disable'
    ),
    RECAPTCHA_PUBLIC_KEY=(
        '',
        'ReCAPTCHA public key, leave empty to disable'
    ),
    RECAPTCHA_PRIVATE_KEY=(
        '',
        'ReCAPTCHA private key, leave empty to disable'
    ),
    EMAIL_LIST_MDN_ADMINS=(
        'mdn-admins@mozilla.org',
        'Email address to request admin intervention'
    ),
)

# Google Analytics Tracking Account Number (0 to disable)
GOOGLE_ANALYTICS_ACCOUNT = config('GOOGLE_ANALYTICS_ACCOUNT', default=None)

KUMASCRIPT_URL_TEMPLATE = config('KUMASCRIPT_URL_TEMPLATE',
                                 default='http://localhost:9080/docs/{path}')

# Elasticsearch related settings.
ES_DEFAULT_NUM_REPLICAS = 1
ES_DEFAULT_NUM_SHARDS = 5
ES_DEFAULT_REFRESH_INTERVAL = '5s'
ES_INDEX_PREFIX = config('ES_INDEX_PREFIX', default='mdn')
ES_INDEXES = {'default': 'main_index'}
# Specify the extra timeout in seconds for the indexing ES connection.
ES_INDEXING_TIMEOUT = 30
ES_LIVE_INDEX = config('ES_LIVE_INDEX', default=False, cast=bool)
ES_URLS = config('ES_URLS', default='127.0.0.1:9200', cast=Csv())


# Logging is merged with the default logging
# https://github.com/django/django/blob/stable/1.11.x/django/utils/log.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'formatters': {
        'simple': {
            'format': '%(name)s:%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'console-simple': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],  # Drop mail_admins
            'level': 'INFO',
        },
        'kuma': {
            'handlers': ['console-simple'],
            'propagate': True,
            'level': 'ERROR',
        },
        'elasticsearch': {
            'handlers': ['console-simple'],
            'level': config('ES_LOG_LEVEL', default='ERROR'),
        },
        'elasticsearch.trace': {
            'handlers': ['console-simple'],
            'level': config('ES_TRACE_LOG_LEVEL', default='ERROR'),
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['console-simple'],
            'level': 'ERROR',
        },
        'cacheback': {
            'handlers': ['console-simple'],
            'level': 'ERROR',
        },
    }
}


CSRF_COOKIE_DOMAIN = DOMAIN
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
# We need to explcitly set the trusted origins, because when CSRF_COOKIE_DOMAIN
# is explicitly set, as we do above, Django's CsrfViewMiddleware will reject
# the request unless the domain of the incoming referer header matches not just
# the CSRF_COOKIE_DOMAIN alone, but the CSRF_COOKIE_DOMAIN with the server port
# appended as well, and we don't want that behavior (a server port of 8000 is
# added both in secure local development as well as in K8s stage/production, so
# that will guarantee a mismatch with the referer).
CSRF_TRUSTED_ORIGINS = [WIKI_HOST, DOMAIN, BETA_HOST]
X_FRAME_OPTIONS = 'DENY'


def get_user_url(user):
    from kuma.core.urlresolvers import reverse
    return reverse('users.user_detail', args=[user.username])


ABSOLUTE_URL_OVERRIDES = {
    'users.user': get_user_url
}

# Set header X-XSS-Protection: 1; mode=block
SECURE_BROWSER_XSS_FILTER = True

# Set header X-Content-Type-Options: nosniff
SECURE_CONTENT_TYPE_NOSNIFF = True

# Set header Strict-Transport-Security header
# 63072000 in production (730 days)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)

# Honor the X-Forwarded-Proto header, to assume HTTPS instead of HTTP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Auth and permissions related constants
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'home'

# django-allauth configuration
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = config('ACCOUNT_DEFAULT_HTTP_PROTOCOL',
                                       default='https')
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_ADAPTER = 'kuma.users.adapters.KumaAccountAdapter'
ACCOUNT_SIGNUP_FORM_CLASS = None
ACCOUNT_UNIQUE_EMAIL = False

SOCIALACCOUNT_ADAPTER = 'kuma.users.adapters.KumaSocialAccountAdapter'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = False  # forces the use of the signup view
SOCIALACCOUNT_QUERY_EMAIL = True  # used by the custom github provider

HONEYPOT_FIELD_NAME = 'website'

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

# TODO: Once using DRF more we need to make that exception handler more generic
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'kuma.search.utils.search_exception_handler'
}

SENTRY_DSN = config('SENTRY_DSN', default=None)

if SENTRY_DSN:
    from raven.transport.requests import RequestsHTTPTransport
    RAVEN_CONFIG = {
        'dsn': SENTRY_DSN,
        'transport': RequestsHTTPTransport,  # Sync transport
        'ignore_exception': [
            'django.core.exceptions.DisallowedHost',
        ],
    }
    if REVISION_HASH and REVISION_HASH != 'undefined':
        RAVEN_CONFIG['release'] = REVISION_HASH
    # Loaded from environment for CSP reporting endpoint
    if SENTRY_ENVIRONMENT:
        RAVEN_CONFIG['environment'] = SENTRY_ENVIRONMENT
    INSTALLED_APPS = INSTALLED_APPS + (
        'raven.contrib.django.raven_compat',
    )

# Tell django-recaptcha we want to use "No CAPTCHA".
# Note: The API keys are located in Django constance.
NOCAPTCHA = True  # Note: Using No Captcha implies SSL.

# Tell django-taggit to use case-insensitive search for existing tags
TAGGIT_CASE_INSENSITIVE = True

# Ad Banner Settings
FOUNDATION_CALLOUT = config('FOUNDATION_CALLOUT', False, cast=bool)
NEWSLETTER = True
NEWSLETTER_ARTICLE = True

# Content Experiments
# Must be kept up to date with PIPELINE_JS setting and the JS client-side
#  configuration. The 'id' should be a key in PIPELINE_JS, that loads
#  Traffic Cop and a client-side configuration like
#  kuma/static/js/experiment-wiki-content.js
# Only one experiment should be active for a given locale and slug.
#
ce_path = path('kuma', 'settings', 'content_experiments.json')
with open(ce_path, 'r') as ce_file:
    CONTENT_EXPERIMENTS = json.load(ce_file)

# django-ratelimit
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)
RATELIMIT_USE_CACHE = config('RATELIMIT_USE_CACHE', default='default')
RATELIMIT_VIEW = 'kuma.core.views.rate_limited'

# Caching constants for the Cache-Control header.
CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE = config(
    'CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE', default=60 * 5, cast=int)

# Stripe API KEY settings
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PRODUCT_ID = config('STRIPE_PRODUCT_ID', default='')
MDN_CONTRIBUTION = config('MDN_CONTRIBUTION', False, cast=bool)
CONTRIBUTION_SUPPORT_EMAIL = config('CONTRIBUTION_SUPPORT_EMAIL',
                                    default='mdn-support@mozilla.com')
if MDN_CONTRIBUTION:
    CSP_CONNECT_SRC.append('https://checkout.stripe.com')
    CSP_FRAME_SRC.append('https://checkout.stripe.com')
    CSP_IMG_SRC.append('https://*.stripe.com')
    CSP_SCRIPT_SRC.append('https://checkout.stripe.com')

# Settings used for communication with the React server side rendering server
SSR_URL = config('SSR_URL', default='http://localhost:8002/ssr')
SSR_TIMEOUT = float(config('SSR_TIMEOUT', default='1'))

# Setting for configuring the AWS S3 bucket name used for the document API.
MDN_API_S3_BUCKET_NAME = config('MDN_API_S3_BUCKET_NAME', default=None)

# When we potentially have multiple CDN distributions that do different
# things.
# Inside kuma, when a document is considered "changed", we trigger
# worker tasks that do things such as publishing/unpublishing to S3.
# Quite agnostic from *how* that works, this list of distributions,
# if they have an 'id', gets called for each (locale, slug) to
# turn that into CloudFront "paths".
# Note that the 'id' is optional because its ultimate value might
# or not might not be in the environment.
MDN_CLOUDFRONT_DISTRIBUTIONS = {
    'api': {
        'id': config('MDN_API_CLOUDFRONT_DISTRIBUTIONID', default=None),
        # TODO We should have a (Django) system check that checks that this
        # transform callable works. For example, it *has* to start with a '/'.
        'transform_function': 'kuma.api.v1.views.get_cdn_key'
    },
    # TODO We should have an entry here for the existing website.
    # At the time of writing we conservatively set the TTL to 5 min.
    # If this CloudFront invalidation really works, we can bump that 5 min
    # to ~60min and put configuration here for it too.

}

# We use django-cacheback for a bunch of tasks. By default, when cacheback,
# has called the `.fetch` of a job class, it calls `cache.set(key, ...)`
# and then it immediately does `cache.get(key)` just to see that the `.set`
# worked.
# See https://bugzilla.mozilla.org/show_bug.cgi?id=1567587 for some more
# details about why we don't want or need this.
CACHEBACK_VERIFY_CACHE_WRITE = False
