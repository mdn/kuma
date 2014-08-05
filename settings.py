# Django settings for kuma project.
import logging
import os
import platform
import json

from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

from sumo_locales import LOCALES

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

ROOT_PACKAGE = os.path.basename(ROOT)

ADMINS = (
    ('MDN devs', 'mdn-dev@mozilla.com'),
)

PROTOCOL = 'https://'
DOMAIN = 'developer.mozilla.org'
SITE_URL = PROTOCOL + DOMAIN
PRODUCTION_URL = SITE_URL
STAGING_URL = PROTOCOL + 'developer.allizom.org'
USE_X_FORWARDED_HOST = True

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'kuma',  # Or path to database file if using sqlite3.
        'USER': '',  # Not used with sqlite3.
        'PASSWORD': '',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    },
}

MIGRATION_DATABASES = {
    'wikidb': {
        'NAME': 'wikidb',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'wikiuser',
        'PASSWORD': 'wikipass',
    },
}

# Cache Settings
CACHE_PREFIX = 'kuma'
CACHE_COUNT_TIMEOUT = 60  # in seconds

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': CACHE_COUNT_TIMEOUT,
        'KEY_PREFIX': CACHE_PREFIX,
    },
    # NOTE: The 'secondary' cache should be the same as 'default' in
    # settings_local. The only reason it exists is because we had some issues
    # with caching, disabled 'default', and wanted to selectively re-enable
    # caching on a case-by-case basis to resolve the issue.
    'secondary': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': CACHE_COUNT_TIMEOUT,
        'KEY_PREFIX': CACHE_PREFIX,
    },
    'memcache': {
        'BACKEND': 'memcached_hashring.backend.MemcachedHashRingCache',
        'TIMEOUT': CACHE_COUNT_TIMEOUT * 60,
        'KEY_PREFIX': CACHE_PREFIX,
        'LOCATION': ['127.0.0.1:11211'],
    },
}

SECONDARY_CACHE_ALIAS = 'secondary'

# Addresses email comes from
DEFAULT_FROM_EMAIL = 'notifications@developer.mozilla.org'
SERVER_EMAIL = 'server-error@developer.mozilla.org'

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

# Supported languages
SUMO_LANGUAGES = (
    'ak', 'ar', 'as', 'ast', 'bg', 'bn-BD', 'bn-IN', 'bs', 'ca', 'cs', 'da',
    'de', 'el', 'en-US', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'fur',
    'fy-NL', 'ga-IE', 'gd', 'gl', 'gu-IN', 'he', 'hi-IN', 'hr', 'hu', 'hy-AM',
    'id', 'ilo', 'is', 'it', 'ja', 'kk', 'kn', 'ko', 'lt', 'mai', 'mk', 'mn',
    'mr', 'ms', 'my', 'nb-NO', 'nl', 'no', 'oc', 'pa-IN', 'pl', 'pt-BR',
    'pt-PT', 'rm', 'ro', 'ru', 'rw', 'si', 'sk', 'sl', 'sq', 'sr-CYRL',
    'sr-LATN', 'sv-SE', 'ta-LK', 'te', 'th', 'tr', 'uk', 'vi', 'zh-CN',
    'zh-TW',
)

# Accepted locales
MDN_LANGUAGES = (
                 'en-US',
                 'ar',
                 'bn-BD',
                 'de',
                 'el',
                 'es',
                 'fa',
                 'fi',
                 'fr',
                 'cs',
                 'ca',
                 'fy-NL',
                 'ga-IE',
                 'he',
                 'hi-IN',
                 'hr',
                 'hu',
                 'id',
                 'it',
                 'ja',
                 'ka',
                 'ko',
                 'ml',
                 'ms',
                 'nl',
                 'pl',
                 'pt-BR',
                 'pt-PT',
                 'ro',
                 'ru',
                 'sq',
                 'ta',
                 'th',
                 'tr',
                 'vi',
                 'zh-CN',
                 'zh-TW'
)

RTL_LANGUAGES = (
                 'ar',
                 'fa',
                 'fa-IR',
                 'he'
)

DEV_POOTLE_PRODUCT_DETAILS_MAP = {
    'pt': 'pt-PT',
    'fy': 'fy-NL',
    'xx-testing': 'x-testing',
}

# Override generic locale handling with explicit mappings.
# Keys are the requested locale; values are the delivered locale.
LOCALE_ALIASES = {
    # Treat "English (United States)" as the canonical "English".
    'en': 'en-US',

    # Create aliases for over-specific locales.
    'bn': 'bn-BD',
    'fy': 'fy-NL',
    'ga': 'ga-IE',
    'gu': 'gu-IN',
    'hi': 'hi-IN',
    'hy': 'hy-AM',
    'pa': 'pa-IN',
    'sv': 'sv-SE',
    'ta': 'ta-LK',

    # Map a prefix to one of its multiple specific locales.
    'pt': 'pt-PT',
    'sr': 'sr-Cyrl',
    'zh': 'zh-CN',

    # Create aliases for locales which do not share a prefix.
    'nb-NO': 'no',
    'nn-NO': 'no',

    # Create aliases for locales which use region subtags to assume scripts.
    'zh-Hans': 'zh-CN',
    'zh-Hant': 'zh-TW',
}

try:
    DEV_LANGUAGES = [
        loc.replace('_','-') for loc in os.listdir(path('locale'))
        if os.path.isdir(path('locale', loc))
            and loc not in ['.svn', '.git', 'templates']
    ]
    for pootle_dir in DEV_LANGUAGES:
        if pootle_dir in DEV_POOTLE_PRODUCT_DETAILS_MAP:
            DEV_LANGUAGES.remove(pootle_dir)
            DEV_LANGUAGES.append(DEV_POOTLE_PRODUCT_DETAILS_MAP[pootle_dir])
except OSError:
    DEV_LANGUAGES = ('en-US',)

PROD_LANGUAGES = MDN_LANGUAGES

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in PROD_LANGUAGES])
for requested_lang, delivered_lang in LOCALE_ALIASES.items():
    if delivered_lang in PROD_LANGUAGES:
        LANGUAGE_URL_MAP[requested_lang.lower()] = delivered_lang

# Override Django's built-in with our native names
def lazy_langs():
    from product_details import product_details
    # for bug 664330
    # from django.conf import settings
    # langs = DEV_LANGUAGES if (getattr(settings, 'DEV', False) or getattr(settings, 'STAGE', False)) else PROD_LANGUAGES
    langs = PROD_LANGUAGES
    return dict([(lang.lower(), product_details.languages[lang]['native'])
                for lang in langs])

LANGUAGES_DICT = lazy(lazy_langs, dict)()
LANGUAGES = sorted(tuple([(i, LOCALES[i].native) for i in MDN_LANGUAGES]),
                   key=lambda lang:lang[0])

# DEKI uses different locale keys
def lazy_language_deki_map():
    # for bug 664330
    # from django.conf import settings
    # langs = DEV_LANGUAGES if (getattr(settings, 'DEV', False) or getattr(settings, 'STAGE', False)) else PROD_LANGUAGES
    langs = PROD_LANGUAGES
    lang_deki_map = dict([(i, i) for i in langs])
    lang_deki_map['en-US'] = 'en'
    lang_deki_map['zh-CN'] = 'cn'
    lang_deki_map['zh-TW'] = 'zh_tw'
    return lang_deki_map

LANGUAGE_DEKI_MAP = lazy(lazy_language_deki_map, dict)()

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
    "en"    : "en-US",
    "ja"    : "ja",
    "pl"    : "pl",
    "fr"    : "fr",
    "es"    : "es",
    ""      : "en-US",
    "cn"    : "zh-CN",
    "zh_cn" : "zh-CN",
    "zh-cn" : "zh-CN",
    "zh_tw" : "zh-TW",
    "zh-tw" : "zh-TW",
    "ko"    : "ko",
    "pt"    : "pt-PT",
    "de"    : "de",
    "it"    : "it",
    "ca"    : "ca",
    "cs"    : "cs",
    "ru"    : "ru",
    "nl"    : "nl",
    "hu"    : "hu",
    "he"    : "he",
    "el"    : "el",
    "fi"    : "fi",
    "tr"    : "tr",
    "vi"    : "vi",
    "ro"    : "ro",
    "ar"    : "ar",
    "th"    : "th",
    "fa"    : "fa",
    "ka"    : "ka",
}

TEXT_DOMAIN = 'messages'

SITE_ID = 1

PROD_DETAILS_DIR = path('../product_details_json')
MDC_PAGES_DIR = path('../mdc_pages')

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = (
    path('locale'),
)

# Use the real robots.txt?
ENGAGE_ROBOTS = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# Absolute path to the directory for the humans.txt file.
HUMANSTXT_ROOT = MEDIA_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATIC_ROOT = path('static')

SERVE_MEDIA = False

# Paths that don't require a locale prefix.
LANGUAGE_URL_IGNORED_PATHS = (
    'media',
    'admin',
    'robots.txt',
    'services',
    'static',
    '1',
    'files',
    '@api',
    'grappelli',
    '__debug__',
    '.well-known',
    'users/persona/login/',
    'users/github/login/callback/',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'jingo.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

JINGO_EXCLUDE_APPS = (
    'admin',
    'grappelli',
    'waffle',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.csrf',
    'django.contrib.messages.context_processors.messages',

    'allauth.account.context_processors.account',
    'allauth.socialaccount.context_processors.socialaccount',

    'sumo.context_processors.global_settings',

    'devmo.context_processors.i18n',
    'devmo.context_processors.next_url',

    'jingo_minify.helpers.build_ids',
    'constance.context_processors.config',
)

MIDDLEWARE_CLASSES = (
    # This gives us atomic success or failure on multi-row writes. It does not
    # give us a consistent per-transaction snapshot for reads; that would need
    # the serializable isolation level (which InnoDB does support) and code to
    # retry transactions that roll back due to serialization failures. It's a
    # possibility for the future. Keep in mind that memcache defeats
    # snapshotted reads where we don't explicitly use the "uncached" manager.
    'django.middleware.transaction.TransactionMiddleware',

    # LocaleURLMiddleware must be before any middleware that uses
    # sumo.urlresolvers.reverse() to add locale prefixes to URLs:
    'sumo.middleware.LocaleURLMiddleware',
    'wiki.middleware.DocumentZoneMiddleware',
    'wiki.middleware.ReadOnlyMiddleware',
    'sumo.middleware.Forbidden403Middleware',
    'django.middleware.common.CommonMiddleware',
    'sumo.middleware.RemoveSlashMiddleware',
    'commonware.middleware.NoVarySessionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sumo.anonymous.AnonymousIdentityMiddleware',
    'sumo.middleware.PlusToSpaceMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'kuma.users.middleware.BanMiddleware',

    'badger.middleware.RecentBadgeAwardsMiddleware',
    'wiki.badges.BadgeAwardingMiddleware',
)

# Auth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'teamwork.backends.TeamworkBackend',
)
AUTH_PROFILE_MODULE = 'users.UserProfile'

PASSWORD_HASHERS = (
    'kuma.users.backends.Sha256Hasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)

USER_AVATAR_PATH = 'uploads/avatars/'
DEFAULT_AVATAR = MEDIA_URL + 'img/avatar.png'
AVATAR_SIZE = 48  # in pixels
ACCOUNT_ACTIVATION_DAYS = 30
MAX_AVATAR_FILE_SIZE = 131072  # 100k, in bytes

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path('templates'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

# TODO: Figure out why changing the order of apps (for example, moving taggit
# higher in the list) breaks tests.
INSTALLED_APPS = (
    # django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',

    'grappelli.dashboard',
    'grappelli',
    'django.contrib.admin',

    'django.contrib.sitemaps',
    'django.contrib.staticfiles',

    # MDN
    'devmo',
    'docs',
    'kuma.feeder',
    'landing',
    'search',
    'kuma.users',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.persona',
    'kuma.users.providers.github',
    'wiki',
    'kuma.events',

    # DEMOS
    'kuma.demos',
    'captcha',
    'contentflagging',
    'actioncounters',
    'threadedcomments',

    # util
    'cronjobs',
    'jingo_minify',
    'product_details',
    'tower',
    'smuggler',
    'constance.backends.database',
    'constance',
    'waffle',
    'soapbox',
    'authkeys',
    'tidings',
    'teamwork',
    'djcelery',
    'taggit',
    'dbgettext',

    'dashboards',
    'kpi',
    'statici18n',
    'rest_framework',

    # migrations
    'south',

    # testing.
    'django_nose',
    'test_utils',

    # other
    'kuma.humans',

    'badger',
)

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

NOSE_ARGS = [
    '--traverse-namespace',  # make sure `./manage.py test kuma` works
]

TEST_UTILS_NO_TRUNCATE = ('django_content_type',)

# Feed fetcher config
FEEDER_TIMEOUT = 6  # in seconds

def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
    from django.core.cache.backends.memcached import CacheClass as MemcachedCacheClass
    from django.core.cache import get_cache
    cache = get_cache('memcache')
    config = {'extensions': ['jinja2.ext.i18n', 'tower.template.i18n',
                             'jinja2.ext.with_', 'jinja2.ext.loopcontrols',
                             'jinja2.ext.autoescape'],
              'finalize': lambda x: x if x is not None else ''}
    if isinstance(cache, MemcachedCacheClass) and not settings.DEBUG:
        # We're passing the _cache object directly to jinja because
        # Django can't store binary directly; it enforces unicode on it.
        # Details: http://jinja.pocoo.org/2/documentation/api#bytecode-cache
        # and in the errors you get when you try it the other way.
        bc = jinja2.MemcachedBytecodeCache(cache._cache,
                                           "%s:j2:" % settings.CACHE_PREFIX)
        config['cache_size'] = -1  # Never clear the cache
        config['bytecode_cache'] = bc
    return config

# Let Tower know about our additional keywords.
# DO NOT import an ngettext variant as _lazy.
TOWER_KEYWORDS = {
    '_lazy': None,
}

# Tells the extract script what files to look for l10n in and what function
# handles the extraction.  The Tower library expects this.
DOMAIN_METHODS = {
    'messages': [
        ('vendor/**', 'ignore'),
        ('apps/access/**', 'ignore'),
        ('apps/dashboards/**', 'ignore'),
        ('apps/kadmin/**', 'ignore'),
        ('apps/sumo/**', 'ignore'),
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
        ('**/templates/**.ltxt',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('media/js/libs/ckeditor/plugins/mdn-link/**.js', 'javascript')
    ],
}

# These domains will not be merged into messages.pot and will use separate PO
# files. See the following URL for an example of how to set these domains
# in DOMAIN_METHODS.
# http://github.com/jbalogh/zamboni/blob/d4c64239c24aa2f1e91276909823d1d1b290f0ee/settings.py#L254
STANDALONE_DOMAINS = [
    'javascript',
    ]

# If you have trouble extracting strings with Tower, try setting this
# to True
TOWER_ADD_HEADERS = True

# Bundles for JS/CSS Minification
JINGO_MINIFY_USE_STATIC = False
CLEANCSS_BIN = '/usr/bin/cleancss'
UGLIFY_BIN = '/usr/bin/uglifyjs'

MINIFY_BUNDLES = {
    'css': {
        'mdn': (
            'redesign/css/font-awesome.css',
            'redesign/css/main.css',
            'redesign/css/badges.css',
        ),
        'jquery-ui': (
            'js/libs/jquery-ui-1.10.3.custom/css/ui-lightness/jquery-ui-1.10.3.custom.min.css',
            'css/jqueryui/moz-jquery-plugins.css',
            'redesign/css/jquery-ui-customizations.css',
        ),
        'demostudio': (
            'css/demos.css',
            'redesign/css/demo-studio.css',
        ),
        'devderby': (
            'css/devderby.css',
        ),
        'home': (
            'redesign/css/home.css',
            'js/libs/owl.carousel/owl-carousel/owl.carousel.css',
            'js/libs/owl.carousel/owl-carousel/owl.theme.css',
        ),
        'search': (
            'redesign/css/search.css',
        ),
        'wiki': (
            'redesign/css/wiki.css',
            'redesign/css/zones.css',
            'redesign/css/diff.css',

            'js/libs/prism/themes/prism.css',
            'js/libs/prism/plugins/line-highlight/prism-line-highlight.css',
            'js/libs/prism/plugins/ie8/prism-ie8.css',
            'js/prism-mdn/plugins/line-numbering/prism-line-numbering.css',
            'js/prism-mdn/components/prism-json.css',
            'redesign/css/wiki-syntax.css',
        ),
        'wiki-edit': (
            'redesign/css/wiki-edit.css',
        ),
        'sphinx': (
            'redesign/css/wiki.css',
            'redesign/css/sphinx.css',
        ),
        'users': (
            'redesign/css/users.css',
        ),
        'tagit': (
            'css/libs/jquery.tagit.css',
        ),
        'promote': (
            'redesign/css/promote.css',
        ),
        'error': (
            'redesign/css/error.css',
        ),
        'error-404': (
            'redesign/css/error.css',
            'redesign/css/error-404.css',
        ),
        'calendar': (
            'redesign/css/calendar.css',
        ),
        'profile': (
            'redesign/css/profile.css',
        ),
        'dashboards': (
            'redesign/css/dashboards.css',
            'redesign/css/diff.css',
        ),
        'newsletter': (
            'redesign/css/newsletter.css',
        ),
        'learn': (
            'redesign/css/learn.css',
        ),
        'submission': (
            'redesign/css/submission.css',
        ),
        'user-banned': (
            'redesign/css/user-banned.css',
        ),
        'error-403-alternate': (
            'redesign/css/error-403-alternate.css',
        ),
    },
    'js': {
        'main': (
            'js/libs/jquery-2.1.0.js',
            'redesign/js/components.js',
            'redesign/js/analytics.js',
            'redesign/js/main.js',
            'redesign/js/badges.js',
        ),
        'home': (
            'js/libs/owl.carousel/owl-carousel/owl.carousel.js',
            'redesign/js/home.js'
        ),
        'popup': (
            'js/libs/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js',
            'js/modal-control.js',
        ),
        'profile': (
            'js/profile.js',
            'js/moz-jquery-plugins.js',
        ),
        'events': (
            'js/libs/jquery.gmap-1.1.0.js',
            'js/calendar.js',
        ),
        'demostudio': (
            'js/libs/jquery.hoverIntent.minified.js',
            'js/libs/jquery.scrollTo-1.4.2-min.js',
            'js/demos.js',
            'js/libs/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js',
            'js/modal-control.js',
        ),
        'demostudio_devderby_landing': (
            'js/demos-devderby-landing.js',
        ),
        'jquery-ui': (
            'js/libs/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js',
            'js/moz-jquery-plugins.js',
        ),
        'libs/tagit': (
            'js/libs/tag-it.js',
        ),
        'search': (
            'redesign/js/search.js',
            'redesign/js/search-navigator.js',
        ),
        'framebuster': (
            'js/framebuster.js',
        ),
        'syntax-prism': (
            'js/libs/prism/prism.js',
            'js/prism-mdn/components/prism-json.js',
            'js/prism-mdn/plugins/line-numbering/prism-line-numbering.js',
            'js/libs/prism/plugins/line-highlight/prism-line-highlight.js',
            'js/syntax-prism.js',
        ),
        'wiki': (
            'redesign/js/search-navigator.js',
            'redesign/js/wiki.js',
        ),
        'wiki-edit': (
            'js/wiki-edit.js',
            'js/libs/tag-it.js',
            'js/wiki-tags-edit.js',
        ),
        'wiki-move': (
            'js/wiki-move.js',
        ),
        'newsletter': (
            'redesign/js/newsletter.js',
        ),
    },
}

#
# Session cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cookie prefix from PHPBB settings.
PHPBB_COOKIE_PREFIX = 'phpbb3_jzxvr'

# Maximum length of the filename. Forms should use this and raise
# ValidationError if the length is exceeded.
# @see http://code.djangoproject.com/ticket/9893
# Columns are 250 but this leaves 50 chars for the upload_to prefix
MAX_FILENAME_LENGTH = 200
MAX_FILEPATH_LENGTH = 250

ATTACHMENT_HOST = 'mdn.mozillademos.org'

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
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/kuma-messages'

# Celery
import djcelery
djcelery.setup_loader()

BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = 'kuma'
BROKER_PASSWORD = 'kuma'
BROKER_VHOST = 'kuma'
CELERY_RESULT_BACKEND = 'amqp'
CELERY_IGNORE_RESULT = True
CELERY_ALWAYS_EAGER = True  # For tests. Set to False for use.
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERYD_LOG_LEVEL = logging.INFO
CELERYD_CONCURRENCY = 4
CELERY_SEND_TASK_SENT_EVENT = True

CELERY_IMPORTS = (
    'devmo.tasks',
    'wiki.tasks',
    'search.tasks',
    'tidings.events',
    'elasticutils.contrib.django.tasks',
)

CELERY_ANNOTATIONS = {
    "elasticutils.contrib.django.tasks.index_objects": {
        "rate_limit": "100/m",
    },
    "elasticutils.contrib.django.tasks.unindex_objects": {
        "rate_limit": "100/m",
    }
}

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# Wiki rebuild settings
WIKI_REBUILD_TOKEN = 'sumo:wiki:full-rebuild'
WIKI_REBUILD_ON_DEMAND = False

# Anonymous user cookie
ANONYMOUS_COOKIE_NAME = 'SUMO_ANONID'
ANONYMOUS_COOKIE_MAX_AGE = 30 * 86400  # Seconds

# Top contributors cache settings
TOP_CONTRIBUTORS_CACHE_KEY = 'sumo:TopContributors'
TOP_CONTRIBUTORS_CACHE_TIMEOUT = 60 * 60 * 12

# Do not change this without also deleting all wiki documents:
WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE


TIDINGS_FROM_ADDRESS = 'notifications@developer.mozilla.org'
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = True

# recaptcha
RECAPTCHA_USE_SSL = False
RECAPTCHA_PRIVATE_KEY = 'SET ME IN SETTINGS_LOCAL'
RECAPTCHA_PUBLIC_KEY = 'SET ME IN SETTINGS_LOCAL'

# content flagging
DEMO_FLAG_REASONS = (
    ('notworking', _('This demo is not working for me')),
    ('inappropriate', _('This demo contains inappropriate content')),
    ('plagarised', _('This demo was not created by the author')),
)

WIKI_FLAG_REASONS = (
    ('bad', _('This article is spam/inappropriate')),
    ('unneeded', _('This article is obsolete/unneeded')),
    ('duplicate', _('This is a duplicate of another article')),
)

FLAG_REASONS = DEMO_FLAG_REASONS + WIKI_FLAG_REASONS

# bit.ly
BITLY_API_KEY = "SET ME IN SETTINGS_LOCAL"
BITLY_USERNAME = "SET ME IN SETTINGS_LOCAL"

GOOGLE_MAPS_API_KEY = "ABQIAAAAijZqBZcz-rowoXZC1tt9iRT5rHVQFKUGOHoyfP_4KyrflbHKcRTt9kQJVST5oKMRj8vKTQS2b7oNjQ"

# demo studio uploads
# Filesystem path where files uploaded for demos will be written
DEMO_UPLOADS_ROOT = path('media/uploads/demos')
# Base URL from where files uploaded for demos will be linked and served
DEMO_UPLOADS_URL = '/media/uploads/demos/'

# Make sure South stays out of the way during testing
SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

# Provide migrations for third-party vendor apps
# TODO: Move migrations for our apps here, rather than living with the app?
SOUTH_MIGRATION_MODULES = {
    'taggit': 'migrations.south.taggit',
    'djcelery': 'migrations.south.djcelery',
}

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
# must be an entry in the CACHES setting!
CONSTANCE_DATABASE_CACHE_BACKEND = 'memcache'

# Settings and defaults controllable by Constance in admin
CONSTANCE_CONFIG = dict(

    DEMOS_DEVDERBY_CURRENT_CHALLENGE_TAG = (
        "challenge:2011:september",
        "Dev derby current challenge"
    ),

    DEMOS_DEVDERBY_PREVIOUS_WINNER_TAG = (
        "system:challenge:firstplace:2011:august",
        "Tag used to find most recent winner for dev derby"
    ),

    DEMOS_DEVDERBY_CHALLENGE_CHOICE_TAGS = (
        ' '.join([
            "challenge:2011:september",
            "challenge:2011:october",
            "challenge:2011:november",
        ]),
        "Dev derby choices displayed on submission form (space-separated tags)"
    ),

    DEMOS_DEVDERBY_PREVIOUS_CHALLENGE_TAGS = (
        ' '.join([
            "challenge:2011:august",
            "challenge:2011:july",
            "challenge:2011:june",
        ]),
        "Dev derby tags for previous challenges (space-separated tags)"
    ),

    DEMOS_DEVDERBY_HOMEPAGE_FEATURED_DEMO = (
        0,
        'The ID of the demo which should be featured on the new homepage structure'
    ),

    BASKET_RETRIES = (
        5,
        'Number of time to retry basket post before giving up.'
    ),
    BASKET_RETRY_WAIT = (
        .5,
        'How long to wait between basket api request retries. '
        'We typically multiply this value by the retry number so, e.g., '
        'the 4th retry waits 4*.5 = 2 seconds.'
    ),
    BASKET_API_KEY = (
        '',
        'API Key to use for basket requests'
    ),

    BETA_GROUP_NAME = (
        'Beta Testers',
        'Name of the django.contrib.auth.models.Group to use as beta testers'
    ),

    KUMA_DOCUMENT_RENDER_TIMEOUT = (
        180.0,
        'Maximum seconds to wait before considering a rendering in progress or '
        'scheduled as failed and allowing another attempt.'
    ),
    KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT = (
        10.0,
        'Maximum seconds to allow a document to spend rendering during the '
        'response cycle before flagging it to be sent to the deferred rendering '
        'queue for future renders.'
    ),

    KUMASCRIPT_TIMEOUT = (
        0.0,
        'Maximum seconds to wait for a response from the kumascript service. '
        'On timeout, the document gets served up as-is and without macro '
        'evaluation as an attempt at graceful failure. NOTE: a value of 0 '
        'disables kumascript altogether.'
    ),
    KUMASCRIPT_MAX_AGE = (
        600,
        'Maximum acceptable age (in seconds) of a cached response from '
        'kumascript. Passed along in a Cache-Control: max-age={value} header, '
        'which tells kumascript whether or not to serve up a cached response.'
    ),

    KUMA_CUSTOM_CSS_PATH = (
        '/en-US/docs/Template:CustomCSS',
        'Path to a wiki document whose raw content will be loaded as a CSS '
        'stylesheet for the wiki base template. Will also cause the ?raw '
        'parameter for this path to send a Content-Type: text/css header. Empty '
        'value disables the feature altogether.',
    ),

    KUMA_CUSTOM_SAMPLE_CSS_PATH = (
        '/en-US/docs/Template:CustomSampleCSS',
        'Path to a wiki document whose raw content will be loaded as a CSS '
        'stylesheet for live sample template. Will also cause the ?raw '
        'parameter for this path to send a Content-Type: text/css header. Empty '
        'value disables the feature altogether.',
    ),

    DIFF_CONTEXT_LINES = (
        0,
        'Number of lines of context to show in diff display.',
    ),

    FEED_DIFF_CONTEXT_LINES = (
        3,
        'Number of lines of context to show in feed diff display.',
    ),

    WIKI_ATTACHMENT_ALLOWED_TYPES = (
        'image/gif image/jpeg image/png image/svg+xml text/html image/vnd.adobe.photoshop',
        'Allowed file types for wiki file attachments',
    ),

    KUMA_WIKI_IFRAME_ALLOWED_HOSTS = (
        '^https?\:\/\/(developer-local.allizom.org|developer-dev.allizom.org|developer.allizom.org|mozillademos.org|testserver|localhost\:8000|(www.)?youtube.com\/embed\/(\.*))',
        'Regex comprised of domain names that are allowed for IFRAME SRCs'
    ),

    GOOGLE_ANALYTICS_ACCOUNT = (
        '0',
        'Google Analytics Tracking Account Number (0 to disable)',
    ),

    OPTIMIZELY_PROJECT_ID = (
        '',
        'The ID value for optimizely Project Code script'
    ),

    BLEACH_ALLOWED_TAGS = (
        json.dumps([
            'a', 'p', 'div',
        ]),
        "JSON array of tags allowed through Bleach",
    ),

    BLEACH_ALLOWED_ATTRIBUTES = (
        json.dumps({
            '*': ['id', 'class', 'style'],
        }),
        "JSON object associating tags with lists of allowed attributes",
    ),

    BLEACH_ALLOWED_STYLES = (
        json.dumps([
            'font-size', 'text-align',
        ]),
        "JSON array listing CSS styles allowed on tags",
    ),

    WIKI_DOCUMENT_TAG_SUGGESTIONS = (
        json.dumps([
            "Accessibility", "AJAX", "API", "Apps",
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

    SEARCH_FILTER_TAG_OPTIONS = (
        json.dumps([
            "Accessibility", "AJAX", "API", "Apps",
            "Canvas", "CSS", "Device", "DOM", "Events",
            "Extensions", "Firefox", "Firefox OS", "Games",
            "Gecko", "Graphics", "Internationalization", "History", "HTML", "HTTP", "JavaScript", "Layout",
            "Localization", "MDN", "Mobile", "Mozilla",
            "Networking", "Persona", "Places", "Plugins", "Protocols",

            "Reference", "Tutorial", "Landing",

            "junk", "NeedsMarkupWork", "NeedsContent", "NeedsExample",
        ]),
        "JSON array of tags that are enabled for search faceting"
    ),

    SESSION_CLEANUP_CHUNK_SIZE = (
        1000,
        'Number of expired sessions to cleanup up in one go.',
    ),

    WELCOME_EMAIL_FROM = (
        "Janet Swisher, MDN Community Manager <no-reply@mozilla.org>",
        'Email address from which welcome emails will be sent',
    ),

)

BASKET_URL = 'https://basket.mozilla.com'
BASKET_APPS_NEWSLETTER = 'app-dev'

KUMASCRIPT_URL_TEMPLATE = 'http://developer.mozilla.org:9080/docs/{path}'

ES_DISABLED = True
ES_LIVE_INDEX = False

LOG_LEVEL = logging.WARN
SYSLOG_TAG = 'http_app_kuma'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            # use from devmo.helpers until we upgrade to django 1.5
            '()': 'devmo.future.filters.RequireDebugTrue',
        },
    },
    'formatters': {
        'default': {
            'format': '{0}: %(asctime)s %(name)s:%(levelname)s %(message)s: '
                      '%(pathname)s:%(lineno)s'.format(SYSLOG_TAG),
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'level': LOG_LEVEL,
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'level': logging.ERROR,
        },
    },
    'loggers': {
        'mdn': {
            'handlers': ['console'],
            'propagate': True,
            # Use the most permissive setting. It is filtered in the handlers.
            'level': logging.DEBUG,
        },
        'cron': {
            'handlers': ['console'],
            'level': logging.INFO,
        },
        'django.request': {
            'handlers': ['console'],
            'propagate': True,
            # Use the most permissive setting. It is filtered in the handlers.
            'level': logging.DEBUG,
        },
        'elasticsearch': {
            'level': logging.ERROR,
            'handlers': ['console'],
        },
    },
}


CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

TEAMWORK_BASE_POLICIES = {
    'anonymous': (
        'wiki.view_document',),
    'authenticated': (
        'wiki.view_document', 'wiki.add_document', 'wiki.add_revision'),
}

GRAPPELLI_ADMIN_TITLE = 'Mozilla Developer Network - Admin'
GRAPPELLI_INDEX_DASHBOARD = 'admin_dashboard.CustomIndexDashboard'

DBGETTEXT_PATH = 'apps/'
DBGETTEXT_ROOT = 'translations'


def get_user_url(user):
    from sumo.urlresolvers import reverse
    return reverse('users.profile', args=[user.username])

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': get_user_url
}

OBI_BASE_URL = 'https://backpack.openbadges.org/'

# Honor the X-Forwarded-Proto header for environments like local dev VM that
# uses Apache mod_proxy instead of mod_wsgi
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Auth and permissions related constants
LOGIN_URL = reverse_lazy('account_login')
LOGOUT_URL = reverse_lazy('account_logout')
LOGIN_REDIRECT_URL = reverse_lazy('home')

# django-allauth configuration
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_ADAPTER = 'kuma.users.adapters.KumaAccountAdapter'
ACCOUNT_SIGNUP_FORM_CLASS = 'kuma.users.forms.SignupForm'
ACCOUNT_UNIQUE_EMAIL = True

SOCIALACCOUNT_ADAPTER = 'kuma.users.adapters.KumaSocialAccountAdapter'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = False  # forces the use of the signup view
SOCIALACCOUNT_QUERY_EMAIL = True  # used by the custom github provider
SOCIALACCOUNT_PROVIDERS = {
    'persona': {
        'REQUEST_PARAMETERS': {
            'siteName': 'Mozilla Developer Network',
            'siteLogo': '/media/redesign/img/opengraph-logo.png',
        }
    }
}
