# Django settings for kitsune project.
from datetime import date
import logging
import os
import platform
import json

from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

from sumo_locales import LOCALES

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

ROOT_PACKAGE = os.path.basename(ROOT)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

SITE_URL = 'https://developer.mozilla.org'
PROTOCOL = 'https://'
DOMAIN = 'developer.mozilla.org'
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

DATABASE_ROUTERS = ('multidb.PinningMasterSlaveRouter',)

# Put the aliases for your slave databases in this list
SLAVE_DATABASES = []

# Dekiwiki has a backend API. protocol://hostname:port
# If set to False, integration with MindTouch / Dekiwiki will be disabled
DEKIWIKI_ENDPOINT = False # 'https://developer-stage9.mozilla.org'
DEKIWIKI_APIKEY = 'SET IN LOCAL SETTINGS'
DEKIWIKI_MOCK = True

# Cache Settings
CACHE_BACKEND = 'locmem://?timeout=86400'
CACHE_PREFIX = 'kuma:'
CACHE_COUNT_TIMEOUT = 60  # seconds

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 60,
        'KEY_PREFIX': 'kuma',
    }
}

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
MDN_LANGUAGES = ('en-US', 'ar', 'bn-BD', 'de', 'el', 'es', 'fa', 'fi', 'fr',
                 'cs', 'ca', 'fy-NL', 'ga-IE', 'he', 'hr', 'hu', 'id', 'it',
                 'ja', 'ka', 'ko', 'ms', 'nl', 'pl', 'pt-BR', 'pt-PT', 'ro',
                 'ru', 'sq', 'th', 'tr', 'vi', 'zh-CN', 'zh-TW')
RTL_LANGUAGES = ('ar', 'fa', 'fa-IR', 'he')

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

def lazy_lang_url_map():
    # for bug 664330
    # from django.conf import settings
    # langs = DEV_LANGUAGES if (getattr(settings, 'DEV', False) or getattr(settings, 'STAGE', False)) else PROD_LANGUAGES
    langs = PROD_LANGUAGES
    lang_url_map = dict([(i.lower(), i) for i in langs])
    for requested_lang in LOCALE_ALIASES:
        delivered_lang = LOCALE_ALIASES[requested_lang]
        if delivered_lang in langs:
            lang_url_map[requested_lang.lower()] = delivered_lang
    return lang_url_map

LANGUAGE_URL_MAP = lazy(lazy_lang_url_map, dict)()

# Override Django's built-in with our native names
def lazy_langs():
    from product_details import product_details
    # for bug 664330
    # from django.conf import settings
    # langs = DEV_LANGUAGES if (getattr(settings, 'DEV', False) or getattr(settings, 'STAGE', False)) else PROD_LANGUAGES
    langs = PROD_LANGUAGES
    return dict([(lang.lower(), product_details.languages[lang]['native'])
                for lang in langs])

LANGUAGES = lazy(lazy_langs, dict)()
LANGUAGE_CHOICES = sorted(tuple([(i, LOCALES[i].native) for i in MDN_LANGUAGES]), key=lambda lang:lang[0])

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
SUPPORTED_NONLOCALES = ('media', 'admin', 'robots.txt', 'services', 'static',
                        '1', 'files', '@api', )

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.csrf',
    'django.contrib.messages.context_processors.messages',

    'sumo.context_processors.global_settings',
    'sumo.context_processors.for_data',

    'devmo.context_processors.i18n',
    'devmo.context_processors.next_url',

    'jingo_minify.helpers.build_ids',

    'constance.context_processors.config',
    'django_browserid.context_processors.browserid_form',
)

MIDDLEWARE_CLASSES = (
    'multidb.middleware.PinningRouterMiddleware',

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
    'wiki.middleware.ReadOnlyMiddleware',
    'sumo.middleware.Forbidden403Middleware',
    'django.middleware.common.CommonMiddleware',
    'sumo.middleware.RemoveSlashMiddleware',
    'inproduct.middleware.EuBuildMiddleware',
    'commonware.middleware.NoVarySessionMiddleware',
    'commonware.middleware.FrameOptionsHeader',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sumo.anonymous.AnonymousIdentityMiddleware',
    'sumo.middleware.PlusToSpaceMiddleware',
    #'dekicompat.middleware.DekiUserMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
)

# Auth
AUTHENTICATION_BACKENDS = (
    'django_browserid.auth.BrowserIDBackend',
    'django.contrib.auth.backends.ModelBackend',
    'dekicompat.backends.DekiUserBackend',
)
AUTH_PROFILE_MODULE = 'devmo.UserProfile'

PASSWORD_HASHERS = (
    'users.backends.Sha256Hasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)

USER_AVATAR_PATH = 'uploads/avatars/'
DEFAULT_AVATAR = MEDIA_URL + 'img/avatar-default.png'
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

# TODO: Figure out why changing the order of apps (for example, moving taggit
# higher in the list) breaks tests.
INSTALLED_APPS = (
    # django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',

    # BrowserID
    'django_browserid',

    # MDN
    'dekicompat',
    'devmo',
    'docs',
    'feeder',
    'landing',

    # DEMOS
    'demos',
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
    'django_statsd',
    'authkeys',

    # SUMO
    'users',
    #'authority',
    #'timezones',
    #'access',
    #'sumo',
    # TODO: Reenable search when we switch to kuma wiki - or, at least waffle it.
    'search',
    'djcelery',
    'notifications',
    'taggit',
    'wiki',
    'dashboards',
    'kpi',
    'gallery',

    # migrations
    'south',

    # testing.
    'django_nose',
    'test_utils',

    # other
    'humans',
)

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'
TEST_UTILS_NO_TRUNCATE = ('django_content_type',)

# Feed fetcher config
FEEDER_TIMEOUT = 6 # in seconds

def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
    from django.core.cache.backends.memcached import CacheClass as MemcachedCacheClass
    from caching.base import cache
    config = {'extensions': ['tower.template.i18n', 'caching.ext.cache',
                             'jinja2.ext.with_', 'jinja2.ext.loopcontrols'],
              'finalize': lambda x: x if x is not None else ''}
    if isinstance(cache, MemcachedCacheClass) and not settings.DEBUG:
        # We're passing the _cache object directly to jinja because
        # Django can't store binary directly; it enforces unicode on it.
        # Details: http://jinja.pocoo.org/2/documentation/api#bytecode-cache
        # and in the errors you get when you try it the other way.
        bc = jinja2.MemcachedBytecodeCache(cache._cache,
                                           "%sj2:" % settings.CACHE_PREFIX)
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
        ('apps/chat/**', 'ignore'),
        ('apps/customercare/**', 'ignore'),
        ('apps/dashboards/**', 'ignore'),
        ('apps/flagit/**', 'ignore'),
        ('apps/forums/**', 'ignore'),
        ('apps/gallery/**', 'ignore'),
        ('apps/inproduct/**', 'ignore'),
        ('apps/kadmin/**', 'ignore'),
        ('apps/kbforums/**', 'ignore'),
        ('apps/questions/**', 'ignore'),
        ('apps/search/**', 'ignore'),
        ('apps/sumo/**', 'ignore'),
        ('apps/tags/**', 'ignore'),
        ('apps/twitter/**', 'ignore'),
        ('apps/upload/**', 'ignore'),
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
    ],
#    'lhtml': [
#        ('apps/forums/**', 'ignore'),
#        ('apps/questions/**', 'ignore'),
#        ('**/templates/**.lhtml',
#            'tower.management.commands.extract.extract_tower_template'),
#    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('media/ckeditor/plugins/mdn-link/**.js', 'javascript'),
        ('media/ckeditor/plugins/mdn-syntaxhighlighter/**.js', 'javascript'),
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
MINIFY_BUNDLES = {
    'css': {
        'mdn': (
            'css/fonts.css',
            'css/mdn-screen.css',
            'css/modals.css',
            'css/mdn-video-player.css',
            'css/mdn-calendar.css',
        ),
        'demostudio': (
            'css/demos.css',
        ),
        'devderby': (
            'css/devderby.css',
        ),
        'common': (
            'css/reset.css',
            'global/headerfooter.css',
            'css/kbox.css',
            'css/main.css',
        ),
        # TODO: remove dependency on jquery ui CSS and use our own
        'jqueryui/jqueryui': (
            'css/jqueryui/jquery-ui-1.8.14.custom.css',
            #'css/jqueryui/jqueryui.css',
        ),
        'questions': (
            'css/to-delete.css',
            'css/tags.css',
        ),
        'search': (
            'css/search.css',
        ),
        'wiki': (
            'css/wiki.css',
            'css/modals.css',
            'css/wiki-screen.css',
            'syntaxhighlighter/styles/shCore.css',
            'syntaxhighlighter/styles/shThemeDefault.css',
            'css/jqueryui/jqueryui.css',
            'css/jqueryui/jquery-ui-1.8.14.custom.css',
            'css/jqueryui/moz-jquery-plugins.css'
        ),
        'wiki-print': (
            'css/wiki-print.css',
        ),
        'dashboards': (
            'css/dashboards.css',
            'js/libs/DataTables-1.9.4/media/css/jquery.dataTables.css',
            'js/libs/DataTables-1.9.4/extras/Scroller/media/css/dataTables.scroller.css',
        ),
        'home': (
            'css/home.css',
        ),
        'gallery': (
            'css/to-delete.css',
            'css/gallery.css',
        ),
        'ie': (
            'css/ie.css',
        ),
        'users': (
            'css/users.css',
        ),
        'monitor': (
            'css/monitor.css',
        ),
        'tagit': (
            'css/jquery.tagit.css',
        ),
    },
    'js': {
        'mdn': (
            'js/jquery-1.9.1.js',
            'js/jquery-upgrade-bridge.js',
            'js/mdn/init.js',
            'js/mdn/gsearch.js',

            # Home Page
            # cycle and slideshow only needed on the home page (or any page
            # featuring the slide show widget).
            'js/mdn/jquery.cycle.js',
            'js/mdn/slideshow.js',

            # Used only on pages with video popups
            'js/mdn/video-player.js',

            'js/mdn/jquery.simplemodal.1.4.1.min.js',
        ),
        'profile': (
            'js/mdn/profile.js',
            'js/moz-jquery-plugins.js',
        ),
        'events': (
            'js/libs/jquery.gmap-1.1.0.js',
            'js/libs/jquery.tablesorter.min.js',
            'js/mdn/calendar.js',
        ),
        'demostudio': (
            'js/mdn/jquery.hoverIntent.minified.js',
            'js/mdn/jquery.scrollTo-1.4.2-min.js',
            'js/mdn/demos.js',
            'js/mdn/modal-control.js'
        ),
        'demostudio_devderby_landing': (
            'js/mdn/demos-devderby-landing.js',
        ),
        'common': (
            'js/libs/jquery.min.js',
            'js/libs/modernizr-1.6.min.js',
        ),
        'libs/jqueryui': (
            'js/libs/jquery-ui-1.8.14.custom.min.js',
        ),
        'libs/tagit': (
            'js/libs/tag-it.js',
        ),
        'questions': (
            'js/libs/jquery.ajaxupload.js',
            'js/tags.js',
        ),
        'search': (
            'js/search.js',
        ),
        'gallery': (
            'js/libs/jquery.ajaxupload.js',
        ),
        'wiki': (
            'js/libs/django/prepopulate.js',
            'syntaxhighlighter/scripts/shCore.js',
            'syntaxhighlighter/scripts/shBrushBash.js',
            'syntaxhighlighter/scripts/shBrushCpp.js',
            'syntaxhighlighter/scripts/shBrushCss.js',
            'syntaxhighlighter/scripts/shBrushJava.js',
            'syntaxhighlighter/scripts/shBrushJScript.js',
            'syntaxhighlighter/scripts/shBrushPhp.js',
            'syntaxhighlighter/scripts/shBrushXml.js',
            'syntaxhighlighter/scripts/shBrushPlain.js',
            'syntaxhighlighter/scripts/shBrushPython.js',
            'js/mdn/jquery.simplemodal.1.4.1.min.js',
            'js/wiki.js',
            'js/main.js',
            'js/libs/jqueryui.min.js',
            'js/moz-jquery-plugins.js',
            'js/libs/tag-it.js',
            'js/wiki-tags-edit.js',
        ),
        'dashboards': (
            'js/libs/jqueryui.min.js',
            'js/moz-jquery-plugins.js',
            'js/libs/DataTables-1.9.4/media/js/jquery.dataTables.js',
            'js/libs/DataTables-1.9.4/extras/Scroller/media/js/dataTables.scroller.js',
        ),
        'customercare': (
            'js/libs/jquery.NobleCount.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.bullseye-1.0.min.js',
            'js/users.js',
        ),
        'users': (
            'js/users.js',
        ),
        'mdn_home': (
            'js/mdn/empty.js',
        ),
        'framebuster': (
            'js/framebuster.js',
        )
    },
}

JAVA_BIN = '/usr/bin/java'

#
# Session cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cookie prefix from PHPBB settings.
PHPBB_COOKIE_PREFIX = 'phpbb3_jzxvr'

#
# Connection information for Sphinx search
SPHINX_HOST = '127.0.0.1'
SPHINX_PORT = 3381
SPHINXQL_PORT = 3382

SPHINX_INDEXER = '/usr/bin/indexer'
SPHINX_SEARCHD = '/usr/bin/searchd'
SPHINX_CONFIG_PATH = path('configs/sphinx/sphinx.conf')

TEST_SPHINX_PATH = path('tmp/test/sphinx')
TEST_SPHINX_PORT = 3416
TEST_SPHINXQL_PORT = 3418

SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 10

# Search default settings
# comma-separated tuple of included category IDs. Negative IDs are excluded.
SEARCH_DEFAULT_CATEGORIES = (10, 20,)
SEARCH_SUMMARY_LENGTH = 275

# The length for which we would like the user to cache search forms and
# results, in minutes.
SEARCH_CACHE_PERIOD = 15

# Maximum length of the filename. Forms should use this and raise
# ValidationError if the length is exceeded.
# @see http://code.djangoproject.com/ticket/9893
# Columns are 250 but this leaves 50 chars for the upload_to prefix
MAX_FILENAME_LENGTH = 200
MAX_FILEPATH_LENGTH = 250
# Default storage engine - ours does not preserve filenames
#DEFAULT_FILE_STORAGE = 'upload.storage.RenameFileStorage'

ATTACHMENT_HOST = 'mdn.mozillademos.org'

# Auth and permissions related constants
LOGIN_URL = '/users/login'
LOGOUT_URL = '/users/logout'
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
REGISTER_URL = '/users/register'

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

# Max number of wiki pages or other questions to suggest might answer the
# question you're about to ask
QUESTIONS_MAX_SUGGESTIONS = 5
# Number of extra suggestion results to pull from Sphinx to make up for
# possibly deleted wiki pages or question. To be safe, set this to the number
# of things that could be deleted between indexer runs.
QUESTIONS_SUGGESTION_SLOP = 3

# Email
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/kuma-messages'

# Read-only mode setup.
READ_ONLY = False


# Turn on read-only mode in settings_local.py by putting this line
# at the VERY BOTTOM: read_only_mode(globals())
def read_only_mode(env):
    env['READ_ONLY'] = True

    # Replace the default (master) db with a slave connection.
    if not env.get('SLAVE_DATABASES'):
        raise Exception("We need at least one slave database.")
    slave = env['SLAVE_DATABASES'][0]
    env['DATABASES']['default'] = env['DATABASES'][slave]

    # No sessions without the database, so disable auth.
    env['AUTHENTICATION_BACKENDS'] = ()

    # Add in the read-only middleware before csrf middleware.
    extra = 'sumo.middleware.ReadOnlyMiddleware'
    before = 'django.middleware.csrf.CsrfViewMiddleware'
    m = list(env['MIDDLEWARE_CLASSES'])
    m.insert(m.index(before), extra)
    env['MIDDLEWARE_CLASSES'] = tuple(m)


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

CELERY_IMPORTS = ( 'wiki.tasks', 'search.tasks' )

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

# Gallery settings
GALLERY_DEFAULT_LANGUAGE = WIKI_DEFAULT_LANGUAGE
GALLERY_IMAGE_PATH = 'uploads/gallery/images/'
GALLERY_IMAGE_THUMBNAIL_PATH = 'uploads/gallery/images/thumbnails/'
GALLERY_VIDEO_PATH = 'uploads/gallery/videos/'
GALLERY_VIDEO_URL = None
GALLERY_VIDEO_THUMBNAIL_PATH = 'uploads/gallery/videos/thumbnails/'
GALLERY_VIDEO_THUMBNAIL_PROGRESS_URL = MEDIA_URL + 'img/video-thumb.png'
THUMBNAIL_PROGRESS_WIDTH = 32  # width of the above image
THUMBNAIL_PROGRESS_HEIGHT = 32  # height of the above image
VIDEO_MAX_FILESIZE = 16777216  # 16 megabytes, in bytes

# Customer Care settings
CC_MAX_TWEETS = 500   # Max. no. of tweets in DB
CC_TWEETS_PERPAGE = 100   # How many tweets to collect in one go. Max: 100.
CC_SHOW_REPLIES = True  # Show replies to tweets?

CC_TWEET_ACTIVITY_URL = 'https://metrics.mozilla.com/stats/twitter/armyOfAwesomeKillRate.json'  # Tweet activity stats
CC_TOP_CONTRIB_URL = 'https://metrics.mozilla.com/stats/twitter/armyOfAwesomeTopSoldiers.json'  # Top contributor stats
CC_TWEET_ACTIVITY_CACHE_KEY = 'sumo-cc-tweet-stats'
CC_TOP_CONTRIB_CACHE_KEY = 'sumo-cc-top-contrib-stats'
CC_STATS_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours
CC_STATS_WARNING = 30 * 60 * 60  # Warn if JSON data is older than 30 hours
CC_IGNORE_USERS = ['fx4status']  # User names whose tweets to ignore.

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''


NOTIFICATIONS_FROM_ADDRESS = 'notifications@support.mozilla.com'
# Anonymous watches must be confirmed.
CONFIRM_ANONYMOUS_WATCHES = True


# URL of the chat server.
CHAT_SERVER = 'https://chat-support.mozilla.com:9091'
CHAT_CACHE_KEY = 'sumo-chat-queue-status'

# recaptcha
RECAPTCHA_USE_SSL = False
RECAPTCHA_PRIVATE_KEY = 'SET ME IN SETTINGS_LOCAL'
RECAPTCHA_PUBLIC_KEY = 'SET ME IN SETTINGS_LOCAL'

# content flagging
FLAG_REASONS = (
    ('notworking', _('This demo is not working for me')),
    ('inappropriate', _('This demo contains inappropriate content')),
    ('plagarised', _('This demo was not created by the author')),
)

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
    # HACK: South treats "database" as the name of constance.backends.database
    'database': 'migrations.south.constance',
    'djcelery': 'migrations.south.djcelery',
}

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_DATABASE_CACHE_BACKEND = None

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

    KUMA_CODE_SAMPLE_HOSTS = (
        ' '.join([
            'developer-local.allizom.org',
            'developer-dev.allizom.org',
            'developer.allizom.org',
            'mozillademos.org',
            'testserver',
            'localhost:8000'
        ]),
        'List of domains from which live code samples may be served '
        '(space-separated)'
    ),

    GOOGLE_ANALYTICS_ACCOUNT = (
        '0',
        'Google Analytics Tracking Account Number (0 to disable)',
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
)

BROWSERID_VERIFICATION_URL = 'https://verifier.login.persona.org/verify'

LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL_FAILURE = '/'

BASKET_URL = 'https://basket.mozilla.com'
BASKET_APPS_NEWSLETTER = 'app-dev'

KUMASCRIPT_URL_TEMPLATE = 'http://developer.mozilla.org:9080/docs/{path}'

STATSD_CLIENT = 'django_statsd.clients.normal'
STATSD_HOST = 'localhost'
STATSD_PORT = 8125
STATSD_PREFIX = 'developer'

GRAPHITE_HOST = 'localhost'
GRAPHITE_PORT = 2003
GRAPHITE_PREFIX = 'devmo'
GRAPHITE_TIMEOUT = 1

ES_DISABLED = True
ES_LIVE_INDEX = False

LOG_LEVEL = logging.WARN
SYSLOG_TAG = 'http_app_kuma'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'mdn_default': {
            'format': ('%s: %%(asctime)s %%(name)s:%%(levelname)s %%(message)s '
                       ':%%(pathname)s:%%(lineno)s' % SYSLOG_TAG),
        },
    },
    'handlers': {
        'mdn_debug': {
            'class': 'logging.StreamHandler',
            'formatter': 'mdn_default',
            'level': LOG_LEVEL,
        },
        'mdn_prod': {
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'mdn_default',
            'level': logging.ERROR,
        },
    },
    'loggers': {
        'mdn': {
            'handlers': ['mdn_prod' if not DEBUG else 'mdn_debug'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}
