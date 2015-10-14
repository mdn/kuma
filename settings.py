# Django settings for kuma project.
from collections import namedtuple
import json
import logging
import os
import platform

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

_Language = namedtuple(u'Language', u'english native iso639_1')


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

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
        'USER': 'kuma',  # Not used with sqlite3.
        'PASSWORD': 'kuma',  # Not used with sqlite3.
        'HOST': 'localhost',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'sql_mode': 'TRADITIONAL',
            'charset': 'utf8',
            'init_command': 'SET '
                'storage_engine=INNODB,'
                'character_set_connection=utf8,'
                'collation_connection=utf8_general_ci',
        },
        'ATOMIC_REQUESTS': True,
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'utf8_general_ci',
        },
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
    'memcache': {
        'BACKEND': 'memcached_hashring.backend.MemcachedHashRingCache',
        'TIMEOUT': CACHE_COUNT_TIMEOUT * 60,
        'KEY_PREFIX': CACHE_PREFIX,
        'LOCATION': ['127.0.0.1:11211'],
    },
}

CACHEBACK_CACHE_ALIAS = 'memcache'

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

# Accepted locales
MDN_LANGUAGES = (
    'en-US',
    'af',
    'ar',
    'az',
    'bm',
    'bn-BD',
    'bn-IN',
    'cs',
    'ca',
    'de',
    'ee',
    'el',
    'es',
    'fa',
    'ff',
    'fi',
    'fr',
    'fy-NL',
    'ga-IE',
    'ha',
    'he',
    'hi-IN',
    'hr',
    'hu',
    'id',
    'ig',
    'it',
    'ja',
    'ka',
    'ko',
    'ln',
    'mg',
    'ml',
    'ms',
    'my',
    'nl',
    'pl',
    'pt-BR',
    'pt-PT',
    'ro',
    'ru',
    'son',
    'sq',
    'sv-SE',
    'sw',
    'ta',
    'th',
    'tl',
    'tn',
    'tr',
    'vi',
    'wo',
    'xh',
    'yo',
    'zh-CN',
    'zh-TW',
    'zu',
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

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in MDN_LANGUAGES])
for requested_lang, delivered_lang in LOCALE_ALIASES.items():
    if delivered_lang in MDN_LANGUAGES:
        LANGUAGE_URL_MAP[requested_lang.lower()] = delivered_lang


def get_locales():
    locales = {}
    file = os.path.join(ROOT, 'kuma', 'languages.json')
    json_locales = json.load(open(file, 'r'))
    for locale, meta in json_locales.items():
        locales[locale] = _Language(meta['English'],
                                    meta['native'],
                                    locale)
    return locales

LOCALES = get_locales()

LANGUAGES = sorted(tuple([(i, LOCALES[i].native) for i in MDN_LANGUAGES]),
                   key=lambda lang: lang[0])

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
    "en": "en-US",
    "ja": "ja",
    "pl": "pl",
    "fr": "fr",
    "es": "es",
    "": "en-US",
    "cn": "zh-CN",
    "zh_cn": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_tw": "zh-TW",
    "zh-tw": "zh-TW",
    "ko": "ko",
    "pt": "pt-PT",
    "de": "de",
    "it": "it",
    "ca": "ca",
    "cs": "cs",
    "ru": "ru",
    "nl": "nl",
    "hu": "hu",
    "he": "he",
    "el": "el",
    "fi": "fi",
    "tr": "tr",
    "vi": "vi",
    "ro": "ro",
    "ar": "ar",
    "th": "th",
    "fa": "fa",
    "ka": "ka",
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
    'contribute.json',
    'services',
    'static',
    '1',
    'files',
    '@api',
    '__debug__',
    '.well-known',
    'users/persona/',
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
    'waffle',
    'registration',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.core.context_processors.csrf',
    'django.contrib.messages.context_processors.messages',

    'kuma.core.context_processors.global_settings',
    'kuma.core.context_processors.i18n',
    'kuma.core.context_processors.next_url',

    'constance.context_processors.config',
)

MIDDLEWARE_CLASSES = (
    # LocaleURLMiddleware must be before any middleware that uses
    # kuma.core.urlresolvers.reverse() to add locale prefixes to URLs:
    'kuma.core.middleware.LocaleURLMiddleware',
    'kuma.core.middleware.SetRemoteAddrFromForwardedFor',
    'kuma.wiki.middleware.DocumentZoneMiddleware',
    'kuma.wiki.middleware.ReadOnlyMiddleware',
    'kuma.core.middleware.Forbidden403Middleware',
    'django.middleware.common.CommonMiddleware',
    'kuma.core.middleware.RemoveSlashMiddleware',
    'commonware.middleware.NoVarySessionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'kuma.core.anonymous.AnonymousIdentityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'kuma.users.middleware.BanMiddleware',
    'waffle.middleware.WaffleMiddleware',
)

# Auth
AUTHENTICATION_BACKENDS = (
    'allauth.account.auth_backends.AuthenticationBackend',
)
AUTH_USER_MODEL = 'users.User'


PASSWORD_HASHERS = (
    'kuma.users.backends.Sha256Hasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)

USER_AVATAR_PATH = 'uploads/avatars/'
DEFAULT_AVATAR = STATIC_URL + 'img/avatar.png'
AVATAR_SIZES = [  # in pixels
    34,   # wiki document page
    48,   # user_link helper
    200,  # user pages
    220,  # default, e.g. used in feeds
]
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
    'pipeline.finders.PipelineFinder',
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

STATICFILES_DIRS = (
    path('kuma', 'static'),
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
    'flat',
    'django.contrib.admin',

    'django.contrib.sitemaps',
    'django.contrib.staticfiles',

    # MDN
    'kuma.core',
    'kuma.feeder',
    'kuma.landing',
    'kuma.search',
    'kuma.users',
    'kuma.wiki',
    'kuma.attachments',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'kuma.users.providers.persona',
    'kuma.users.providers.github',

    # DEMOS
    'kuma.demos',
    'kuma.contentflagging',
    'kuma.actioncounters',

    # util
    'pipeline',
    'product_details',
    'tower',
    'smuggler',
    'constance.backends.database',
    'constance',
    'waffle',
    'soapbox',
    'kuma.authkeys',
    'tidings',
    'djcelery',
    'taggit',
    'dbgettext',
    'honeypot',
    'cacheback',

    'kuma.dashboards',
    'statici18n',
    'rest_framework',

    # testing.
    'django_nose',

    # other
    'kuma.humans',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--traverse-namespace',  # make sure `./manage.py test kuma` works
]

# Feed fetcher config
FEEDER_TIMEOUT = 6  # in seconds


def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
    from django.core.cache.backends.memcached import MemcachedCache
    from django.core.cache import caches
    cache = caches['memcache']
    config = {'extensions': ['jinja2.ext.i18n', 'tower.template.i18n',
                             'jinja2.ext.with_', 'jinja2.ext.loopcontrols',
                             'jinja2.ext.autoescape',
                             'pipeline.templatetags.ext.PipelineExtension'],
              'finalize': lambda x: x if x is not None else ''}
    if isinstance(cache, MemcachedCache) and not settings.DEBUG:
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
        ('kuma/dashboards/**', 'ignore'),
        ('kuma/core/**', 'ignore'),
        ('kuma/**.py',
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
STATICI18N_DOMAIN = 'javascript'

# If you have trouble extracting strings with Tower, try setting this
# to True
TOWER_ADD_HEADERS = True

PIPELINE_COMPILERS = (
    'pipeline.compilers.stylus.StylusCompiler',
)

PIPELINE_CSS_COMPRESSOR = 'compressors.cleancss.CleanCSSCompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.uglifyjs.UglifyJSCompressor'

PIPELINE_CSS = {
    'mdn': {
        'source_filenames': (
            'styles/font-awesome.styl',
            'styles/main.styl',
        ),
        'output_filename': 'build/styles/mdn.css',
    },
    'jquery-ui': {
        'source_filenames': (
            'js/libs/jquery-ui-1.10.3.custom/css/ui-lightness/jquery-ui-1.10.3.custom.min.css',
            'styles/libs/jqueryui/moz-jquery-plugins.css',
            'styles/jquery-ui-customizations.styl',
        ),
        'output_filename': 'build/styles/jquery-ui.css',
    },
    'demostudio': {
        'source_filenames': (
            'styles/demos.styl',
        ),
        'output_filename': 'build/styles/demostudio.css',
    },
    'devderby': {
        'source_filenames': (
            'styles/devderby.styl',
        ),
        'output_filename': 'build/styles/devderby.css',
    },
    'gaia': {
        'source_filenames': (
            'styles/gaia.styl',
        ),
        'output_filename': 'build/styles/gaia.css',
    },
    'home': {
        'source_filenames': (
            'styles/home.styl',
        ),
        'output_filename': 'build/styles/home.css',
    },
    'search': {
        'source_filenames': (
            'styles/search.styl',
        ),
        'output_filename': 'build/styles/search.css',
    },
    'search-suggestions': {
        'source_filenames': (
            'styles/search-suggestions.styl',
        ),
        'output_filename': 'build/styles/search-suggestions.css',
    },
    'wiki': {
        'source_filenames': (
            'styles/wiki.styl',
            'styles/zones.styl',
            'styles/diff.styl',

            'js/libs/prism/themes/prism.css',
            'js/libs/prism/plugins/line-highlight/prism-line-highlight.css',
            'js/libs/prism/plugins/ie8/prism-ie8.css',
            'js/prism-mdn/plugins/line-numbering/prism-line-numbering.css',
            'js/prism-mdn/components/prism-json.css',
            'styles/wiki-syntax.styl',
        ),
        'output_filename': 'build/styles/wiki.css',
    },
    'wiki-revisions': {
        'source_filenames': (
            'styles/wiki-revisions.styl',
        ),
        'output_filename': 'build/styles/wiki-revisions.css',
    },
    'wiki-edit': {
        'source_filenames': (
            'styles/wiki-edit.styl',
        ),
        'output_filename': 'build/styles/wiki-edit.css',
    },
    'wiki-compat-tables': {
        'source_filenames': (
            'styles/wiki-compat-tables.styl',
        ),
        'output_filename': 'build/styles/wiki-compat-tables.css',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    'sphinx': {
        'source_filenames': (
            'styles/wiki.styl',
            'styles/sphinx.styl',
        ),
        'output_filename': 'build/styles/sphinx.css',
    },
    'users': {
        'source_filenames': (
            'styles/users.styl',
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
            'styles/promote.styl',
        ),
        'output_filename': 'build/styles/promote.css',
    },
    'error': {
        'source_filenames': (
            'styles/error.styl',
        ),
        'output_filename': 'build/styles/error.css',
    },
    'error-404': {
        'source_filenames': (
            'styles/error.styl',
            'styles/error-404.styl',
        ),
        'output_filename': 'build/styles/error-404.css',
    },
    'dashboards': {
        'source_filenames': (
            'styles/dashboards.styl',
            'styles/diff.styl',
        ),
        'output_filename': 'build/styles/dashboards.css',
    },
    'newsletter': {
        'source_filenames': (
            'styles/newsletter.styl',
        ),
        'output_filename': 'build/styles/newsletter.css',
    },
    'submission': {
        'source_filenames': (
            'styles/submission.styl',
        ),
        'output_filename': 'build/styles/submission.css',
    },
    'user-banned': {
        'source_filenames': (
            'styles/user-banned.styl',
        ),
        'output_filename': 'build/styles/user-banned.css',
    },
    'error-403-alternate': {
        'source_filenames': (
            'styles/error-403-alternate.styl',
        ),
        'output_filename': 'build/styles/error-403-alternate.css',
    },
    'fellowship': {
        'source_filenames': (
            'styles/fellowship.styl',
        ),
        'output_filename': 'build/styles/fellowship.css',
    },
    'mdn10': {
        'source_filenames': (
            'styles/mdn10.styl',
        ),
        'output_filename': 'build/styles/mdn10.css',
    },
    'editor-content': {
        'source_filenames': (
            'styles/main.css',
            'styles/wiki.css',
            'styles/wiki-wysiwyg.css',
            'styles/wiki-syntax.css',
            'styles/libs/font-awesome/css/font-awesome.min.css',
        ),
        'output_filename': 'build/styles/editor-content.css',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    'demowrap': {
        'source_filenames': (
            'styles/demowrap.styl',
            'styles/demos_wrap.styl',
        ),
        'output_filename': 'build/styles/demowrap.css',
    },
}

PIPELINE_JS = {
    'main': {
        'source_filenames': (
            'js/libs/jquery-2.1.0.js',
            'js/components.js',
            'js/analytics.js',
            'js/main.js',
            'js/auth.js',
            'js/libs/fontfaceobserver/fontfaceobserver-standalone.js',
            'js/fonts.js',
        ),
        'output_filename': 'build/js/main.js',
    },
    'popup': {
        'source_filenames': (
            'js/libs/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js',
            'js/modal-control.js',
        ),
        'output_filename': 'build/js/popup.js',
    },
    'users': {
        'source_filenames': (
            'js/libs/tag-it.js',
            'js/users.js',
            'js/moz-jquery-plugins.js',
        ),
        'output_filename': 'build/js/users.js',
        'extra_context': {
            'async': True,
        },
    },
    'social': {
        'source_filenames': (
            'js/social.js',
        ),
        'output_filename': 'build/js/social.js',
        'extra_context': {
            'async': True,
        },
    },
    'helpfulness': {
        'source_filenames': (
            'js/helpfulness.js',
        ),
        'output_filename': 'build/js/helpfulness.js',
        'extra_context': {
            'async': True,
        },
    },
    'demostudio': {
        'source_filenames': (
            'js/libs/jquery.hoverIntent.minified.js',
            'js/libs/jquery.scrollTo-1.4.2-min.js',
            'js/demos.js',
            'js/libs/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js',
            'js/modal-control.js',
        ),
        'output_filename': 'build/js/demostudio.js',
        'extra_context': {
            'async': True,
        },
    },
    'demostudio_devderby_landing': {
        'source_filenames': (
            'js/demos-devderby-landing.js',
        ),
        'output_filename': 'build/js/demostudio_devderby_landing.js',
    },
    'jquery-ui': {
        'source_filenames': (
            'js/libs/jquery-ui-1.10.3.custom/js/jquery-ui-1.10.3.custom.min.js',
            'js/moz-jquery-plugins.js',
        ),
        'output_filename': 'build/js/jquery-ui.js',
    },
    'search': {
        'source_filenames': (
            'js/search.js',
            'js/search-navigator.js',
        ),
        'output_filename': 'build/js/search.js',
        'extra_context': {
            'async': True,
        },
    },
    'framebuster': {
        'source_filenames': (
            'js/framebuster.js',
        ),
        'output_filename': 'build/js/framebuster.js',
    },
    'syntax-prism': {
        'source_filenames': (
            'js/libs/prism/prism.js',
            'js/prism-mdn/components/prism-json.js',
            'js/prism-mdn/plugins/line-numbering/prism-line-numbering.js',
            'js/libs/prism/plugins/line-highlight/prism-line-highlight.js',
            'js/syntax-prism.js',
        ),
        'output_filename': 'build/js/syntax-prism.js',
        'template_name': 'pipeline/javascript-array.jinja',
    },
    'search-suggestions': {
        'source_filenames': (
            'js/search-suggestions.js',
        ),
        'output_filename': 'build/js/search-suggestions.js',
    },
    'wiki': {
        'source_filenames': (
            'js/search-navigator.js',
            'js/wiki.js',
            'js/wiki-samples.js',
        ),
        'output_filename': 'build/js/wiki.js',
        'extra_context': {
            'async': True,
        },
    },
    'wiki-edit': {
        'source_filenames': (
            'js/wiki-edit.js',
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
    'newsletter': {
        'source_filenames': (
            'js/newsletter.js',
        ),
        'output_filename': 'build/js/newsletter.js',
        'extra_context': {
            'async': True,
        },
    },
    'fellowship': {
        'source_filenames': (
            'js/fellowship.js',
        ),
        'output_filename': 'build/js/fellowship.js',
        'extra_context': {
            'async': True,
        },
    },
    'ckeditor-prod': {
        'source_filenames': (
            'js/libs/ckeditor/build/ckeditor/ckeditor.js',
            'js/libs/ckeditor/build/ckeditor/adapters/jquery.js',
        ),
        'output_filename': 'build/js/ckeditor-prod.js',
    },
    'ckeditor-dev': {
        'source_filenames': (
            'js/libs/ckeditor/source/ckeditor/ckeditor.js',
            'js/libs/ckeditor/source/ckeditor/adapters/jquery.js',
        ),
        'output_filename': 'build/js/ckeditor-dev.js',
    },
    'carousel': {
        'source_filenames': (
            'js/libs/carousel.js',
        ),
        'output_filename': 'build/js/carousel.js',
    },
    'html5': {
        'source_filenames': (
            'js/libs/html5.js',
        ),
        'output_filename': 'build/js/html5.js',
    },
    'selectivizr': {
        'source_filenames': (
            'js/libs/selectivizr-1.0.2/selectivizr-build.js',
        ),
        'output_filename': 'build/js/selectivizr.js',
    },
    'hoverIntent': {
        'source_filenames': (
            'js/libs/jquery.hoverIntent.minified.js',
        ),
        'output_filename': 'build/js/hoverIntent.js',
    },
    'modal-control': {
        'source_filenames': (
            'js/modal-control.js',
        ),
        'output_filename': 'build/js/modal-control.js',
    },
    'ace': {
        'source_filenames': (
            'js/libs/ace/ace.js',
            'js/libs/ace/mode-javascript.js',
            'js/libs/ace/theme-dreamweaver.js',
            'js/libs/ace/worker-javascript.js',
        ),
        'output_filename': 'build/js/ace.js',
    },
}

#
# Session cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

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

BROKER_URL = 'amqp://kuma:kuma@developer-local:5672/kuma'

CELERY_ALWAYS_EAGER = True  # For tests. Set to False for use.
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True
CELERY_TRACK_STARTED = True

CELERYD_LOG_LEVEL = logging.INFO
CELERYD_CONCURRENCY = 4

CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERY_ACCEPT_CONTENT = ['pickle']

CELERY_IMPORTS = (
    'tidings.events',
)

CELERY_ANNOTATIONS = {
    'cacheback.tasks.refresh_cache': {
        'rate_limit': '120/m',
    }
}

CELERY_ROUTES = {
    'cacheback.tasks.refresh_cache': {
        'queue': 'mdn_purgeable'
    },
    'kuma.actioncounters.tasks.update_actioncounter_counts': {
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
    'kuma.wiki.tasks.update_community_stats': {
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
    'kuma.users.tasks.email_render_document_progress': {
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
    'kuma.wiki.tasks.render_stale_documents': {
        'queue': 'mdn_wiki'
    },
    'kuma.wiki.tasks.build_json_data_for_document': {
        'queue': 'mdn_wiki'
    },
}

# Wiki rebuild settings
WIKI_REBUILD_TOKEN = 'kuma:wiki:full-rebuild'
WIKI_REBUILD_ON_DEMAND = False

# Anonymous user cookie
ANONYMOUS_COOKIE_NAME = 'KUMA_ANONID'
ANONYMOUS_COOKIE_MAX_AGE = 30 * 86400  # Seconds

# Top contributors cache settings
TOP_CONTRIBUTORS_CACHE_KEY = 'kuma:TopContributors'
TOP_CONTRIBUTORS_CACHE_TIMEOUT = 60 * 60 * 12

# Do not change this without also deleting all wiki documents:
WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE


TIDINGS_FROM_ADDRESS = 'notifications@developer.mozilla.org'
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = True


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
BITLY_API_KEY = None  # Set me in settings_local.py.
BITLY_USERNAME = None  # Set me in settings_local.py.

GOOGLE_MAPS_API_KEY = "ABQIAAAAijZqBZcz-rowoXZC1tt9iRT5rHVQFKUGOHoyfP_4KyrflbHKcRTt9kQJVST5oKMRj8vKTQS2b7oNjQ"

# demo studio uploads
# Filesystem path where files uploaded for demos will be written
DEMO_UPLOADS_ROOT = path('media/uploads/demos')
# Base URL from where files uploaded for demos will be linked and served
DEMO_UPLOADS_URL = MEDIA_URL + 'uploads/demos/'

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
# must be an entry in the CACHES setting!
CONSTANCE_DATABASE_CACHE_BACKEND = 'memcache'

# Settings and defaults controllable by Constance in admin
CONSTANCE_CONFIG = dict(
    DEMO_BLACKLIST_OVERRIDE_EXTENSIONS=(
        'jsgz datagz memgz',
        'File extensions that override the mimetype blacklist in case of '
        'an ambigous mimetype such as application/gzip',
    ),
    DEMO_MAX_ZIP_FILESIZE=(
        60 * 1024 * 1024,
        "Max file size for zips uploaded to demo studio."
    ),
    DEMO_MAX_FILESIZE_IN_ZIP=(
        60 * 1024 * 1024,
        "Max file size for files inside zip uploaded to demo studio."
    ),
    DEMOS_DEVDERBY_CURRENT_CHALLENGE_TAG=(
        "challenge:2011:september",
        "Dev derby current challenge"
    ),
    DEMOS_DEVDERBY_PREVIOUS_WINNER_TAG=(
        "system:challenge:firstplace:2011:august",
        "Tag used to find most recent winner for dev derby"
    ),
    DEMOS_DEVDERBY_CHALLENGE_CHOICE_TAGS=(
        ' '.join([
            "challenge:2011:september",
            "challenge:2011:october",
            "challenge:2011:november",
        ]),
        "Dev derby choices displayed on submission form (space-separated tags)"
    ),
    DEMOS_DEVDERBY_PREVIOUS_CHALLENGE_TAGS=(
        ' '.join([
            "challenge:2013:june",
            "challenge:2013:may",
            "challenge:2013:april",
            "challenge:2013:march",
            "challenge:2013:february",
            "challenge:2013:january",
            "challenge:2012:december",
            "challenge:2012:november",
            "challenge:2012:october",
            "challenge:2012:september",
            "challenge:2012:august",
            "challenge:2012:july",
            "challenge:2012:june",
            "challenge:2012:may",
            "challenge:2012:april",
            "challenge:2012:march",
            "challenge:2012:february",
            "challenge:2012:january",
            "challenge:2011:december",
            "challenge:2011:november",
            "challenge:2011:october",
            "challenge:2011:september",
            "challenge:2011:august",
            "challenge:2011:july",
            "challenge:2011:june",
        ]),
        "Dev derby tags for previous challenges (space-separated tags)"
    ),
    DEMOS_DEVDERBY_HOMEPAGE_FEATURED_DEMO=(
        0,
        'The ID of the demo which should be featured on the new homepage structure'
    ),
    BASKET_RETRIES=(
        5,
        'Number of time to retry basket post before giving up.'
    ),
    BASKET_RETRY_WAIT=(
        .5,
        'How long to wait between basket api request retries. '
        'We typically multiply this value by the retry number so, e.g., '
        'the 4th retry waits 4*.5 = 2 seconds.'
    ),
    BASKET_API_KEY=(
        '',
        'API Key to use for basket requests'
    ),
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
    KUMA_CUSTOM_CSS_PATH=(
        '/en-US/docs/Template:CustomCSS',
        'Path to a wiki document whose raw content will be loaded as a CSS '
        'stylesheet for the wiki base template. Will also cause the ?raw '
        'parameter for this path to send a Content-Type: text/css header. Empty '
        'value disables the feature altogether.',
    ),
    KUMA_CUSTOM_SAMPLE_CSS_PATH=(
        '/en-US/docs/Template:CustomSampleCSS',
        'Path to a wiki document whose raw content will be loaded as a CSS '
        'stylesheet for live sample template. Will also cause the ?raw '
        'parameter for this path to send a Content-Type: text/css header. Empty '
        'value disables the feature altogether.',
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
    KUMA_WIKI_IFRAME_ALLOWED_HOSTS=(
        '^https?\:\/\/(developer-local.allizom.org|developer.allizom.org|mozillademos.org|testserver|localhost\:8000|(www.)?youtube.com\/embed\/(\.*))',
        'Regex comprised of domain names that are allowed for IFRAME SRCs'
    ),
    GOOGLE_ANALYTICS_ACCOUNT=(
        '0',
        'Google Analytics Tracking Account Number (0 to disable)',
    ),
    OPTIMIZELY_PROJECT_ID=(
        '',
        'The ID value for optimizely Project Code script'
    ),
    BLEACH_ALLOWED_TAGS=(
        json.dumps([
            'a', 'p', 'div',
        ]),
        "JSON array of tags allowed through Bleach",
    ),
    BLEACH_ALLOWED_ATTRIBUTES=(
        json.dumps({
            '*': ['id', 'class', 'style', 'lang'],
        }),
        "JSON object associating tags with lists of allowed attributes",
    ),
    BLEACH_ALLOWED_STYLES=(
        json.dumps([
            'font-size', 'text-align',
        ]),
        "JSON array listing CSS styles allowed on tags",
    ),
    WIKI_DOCUMENT_TAG_SUGGESTIONS=(
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
    SEARCH_FILTER_TAG_OPTIONS=(
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
    SESSION_CLEANUP_CHUNK_SIZE=(
        1000,
        'Number of expired sessions to cleanup up in one go.',
    ),
    WELCOME_EMAIL_FROM=(
        "Janet Swisher <no-reply@mozilla.org>",
        'Email address from which welcome emails will be sent',
    ),
    EMAIL_LIST_FOR_FIRST_EDITS=(
        "mdn-spam-watch@mozilla.com",
        "Email address to which emails will be sent for users' first edits",
    ),
)

BASKET_URL = 'https://basket.mozilla.com'
BASKET_APPS_NEWSLETTER = 'app-dev'

KUMASCRIPT_URL_TEMPLATE = 'http://developer.mozilla.org:9080/docs/{path}'

# Elasticsearch related settings.
ES_DEFAULT_NUM_REPLICAS = 1
ES_DEFAULT_NUM_SHARDS = 5
ES_DEFAULT_REFRESH_INTERVAL = '5s'
ES_DISABLED = True
ES_INDEX_PREFIX = 'mdn'
ES_INDEXES = {'default': 'main_index'}
# Specify the extra timeout in seconds for the indexing ES connection.
ES_INDEXING_TIMEOUT = 30
ES_LIVE_INDEX = False
ES_URLS = ['localhost:9200']

LOG_LEVEL = logging.WARN
SYSLOG_TAG = 'http_app_kuma'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
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
            'formatter': 'default',
            'level': LOG_LEVEL,
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'level': logging.ERROR,
        },
    },
    'loggers': {
        'kuma': {
            'handlers': ['console'],
            'propagate': True,
            'level': logging.ERROR,
        },
        'django.request': {
            'handlers': ['console'],
            'propagate': True,
            'level': logging.ERROR,
        },
        'elasticsearch': {
            'handlers': ['console'],
            'level': logging.ERROR,
        },
        'urllib3': {
            'handlers': ['console'],
            'level': logging.ERROR,
        },
        'cacheback': {
            'handlers': ['console'],
            'level': logging.ERROR,
        }
    },
}

CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

DBGETTEXT_PATH = 'kuma/core/'
DBGETTEXT_ROOT = 'translations'


def get_user_url(user):
    from kuma.core.urlresolvers import reverse
    return reverse('users.user_detail', args=[user.username])

ABSOLUTE_URL_OVERRIDES = {
    'users.user': get_user_url
}

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
ACCOUNT_SIGNUP_FORM_CLASS = 'kuma.users.forms.NewsletterForm'  # weird but needed
ACCOUNT_UNIQUE_EMAIL = False

SOCIALACCOUNT_ADAPTER = 'kuma.users.adapters.KumaSocialAccountAdapter'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = False  # forces the use of the signup view
SOCIALACCOUNT_QUERY_EMAIL = True  # used by the custom github provider
SOCIALACCOUNT_PROVIDERS = {
    'persona': {
        'AUDIENCE': 'https://developer.mozilla.org',
        'REQUEST_PARAMETERS': {
            'siteName': 'Mozilla Developer Network',
            'siteLogo': STATIC_URL + 'img/opengraph-logo.png',
        }
    }
}
PERSONA_VERIFIER_URL = 'https://verifier.login.persona.org/verify'
PERSONA_INCLUDE_URL = 'https://login.persona.org/include.js'

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
