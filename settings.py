# Django settings for kitsune project.
import platform
import os
import logging

from tower import ugettext_lazy as _lazy

from sumo_locales import LOCALES

DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOG_LEVEL = logging.DEBUG

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

ROOT_PACKAGE = os.path.basename(ROOT)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'kitsune',  # Or path to database file if using sqlite3.
        'USER': '',  # Not used with sqlite3.
        'PASSWORD': '',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    }
}

DATABASE_ROUTERS = ('multidb.PinningMasterSlaveRouter',)

# Put the aliases for your slave databases in this list
SLAVE_DATABASES = []

# Cache Settings
#CACHE_BACKEND = 'caching.backends.memcached://localhost:11211'
#CACHE_PREFIX = 'sumo:'

# Addresses email comes from
DEFAULT_FROM_EMAIL = 'notifications@support.mozilla.com'
SERVER_EMAIL = 'server-error@support.mozilla.com'

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
    'id', 'ilo', 'is', 'it', 'ja', 'kk', 'kn', 'ko', 'lt', 'mk', 'mn', 'mr',
    'ms', 'nb-NO', 'nl', 'no', 'oc', 'pa-IN', 'pl', 'pt-BR', 'pt-PT', 'rm',
    'ro', 'ru', 'rw', 'si', 'sk', 'sl', 'sq', 'sr-CYRL', 'sr-LATN', 'sv-SE',
    'ta-LK', 'te', 'th', 'tr', 'uk', 'vi', 'zh-CN', 'zh-TW',
)

LANGUAGE_CHOICES = tuple([(i, LOCALES[i].native) for i in SUMO_LANGUAGES])
LANGUAGES = dict([(i.lower(), LOCALES[i].native) for i in SUMO_LANGUAGES])

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in SUMO_LANGUAGES])

TEXT_DOMAIN = 'messages'

SITE_ID = 1
SITE_TITLE = _lazy(u'Firefox Support', 'site_title')


# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Paths that don't require a locale prefix.
SUPPORTED_NONLOCALES = ('media', 'admin')

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',

    'sumo.context_processors.global_settings',
    'sumo.context_processors.for_data',
    'jingo_minify.helpers.build_ids',
    'csrf_context.csrf',
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
    'sumo.middleware.Forbidden403Middleware',
    'django.middleware.common.CommonMiddleware',
    'sumo.middleware.NoCacheHttpsMiddleware',
    'commonware.middleware.NoVarySessionMiddleware',
    'commonware.middleware.FrameOptionsHeader',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sumo.anonymous.AnonymousIdentityMiddleware',

    # TODO: Replace with Kitsune auth.
    'sumo.middleware.TikiCookieMiddleware',

    'twitter.middleware.SessionMiddleware',
    'sumo.middleware.PlusToSpaceMiddleware',
)

# Auth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'sumo.backends.SessionBackend',  # TODO: Replace with Kitsune auth.
)

ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path('templates'),
)

# TODO: Figure out why changing the order of apps (for example, moving taggit
# higher in the list) breaks tests.
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'tower',
    'jingo_minify',
    ROOT_PACKAGE,
    'authority',
    'access',
    'sumo',
    'search',
    'forums',
    'djcelery',
    'cronjobs',
    'notifications',
    'identicons',
    'questions',
    'kadmin',
    'taggit',
    'flagit',
    'upload',
    'product_details',
    'wiki',
    'kbforums',
    'dashboards',
    'gallery',
    'customercare',
    'twitter',
    'chat',
)

# Extra apps for testing
if DEBUG:
    INSTALLED_APPS += (
        'django_extensions',
        'django_nose',
        'test_utils',
    )

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'
TEST_UTILS_NO_TRUNCATE = ('django_content_type',)


def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
    from caching.base import cache
    config = {'extensions': ['tower.template.i18n', 'caching.ext.cache',
                             'jinja2.ext.with_'],
              'finalize': lambda x: x if x is not None else ''}
    if 'memcached' in cache.scheme and not settings.DEBUG:
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
        ('apps/forums/**', 'ignore'),
        ('apps/questions/**', 'ignore'),
        ('apps/chat/**', 'ignore'),
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'lhtml': [
        ('apps/forums/**', 'ignore'),
        ('apps/questions/**', 'ignore'),
        ('**/templates/**.lhtml',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('media/js/*.js', 'javascript'),
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
        'common': (
            'css/main.css',
            'css/sidebar.css',
        ),
        'forums': (
            'css/forums.css',
        ),
        'questions': (
            'css/to-delete.css',
            'css/questions.css',
            'css/tags.css',
            'css/jqueryui/jquery.ui.core.css',
            'css/jqueryui/jquery.ui.autocomplete.css',
            'css/jqueryui/jquery.ui.theme.css',
        ),
        'search': (
            'css/search.css',
        ),
        'wiki': (
            'css/wiki.css',
            # The dashboard app uses the wiki bundle because only the wiki app
            # has the new theme at the moment.
            'css/dashboards.css',
            'css/screencast.css',
            'css/tags.css',
            'css/jqueryui/jquery.ui.core.css',
            'css/jqueryui/jquery.ui.autocomplete.css',
            'css/jqueryui/jquery.ui.theme.css',
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
        'customercare': (
            'css/jqueryui/jquery.ui.core.css',
            'css/jqueryui/jquery.ui.theme.css',
            'css/customercare.css',
        ),
        'chat': (
            'css/chat.css',
        ),
    },
    'js': {
        'common': (
            'js/libs/jquery.min.js',
            'js/libs/modernizr-1.5.min.js',
            'js/menu.js',
            'js/main.js',
        ),
        'questions': (
            'js/libs/jqueryui.min.js',
            'js/markup.js',
            'js/libs/jquery.ajaxupload.js',
            'js/upload.js',
            'js/questions.js',
            'js/tags.js',
        ),
        'search': (
            'js/libs/jqueryui.min.js',
            'js/search.js',
        ),
        'forums': (
            'js/markup.js',
            'js/forums.js',
        ),
        'gallery': (
            'js/libs/jquery.ajaxupload.js',
            'js/gallery.js',
        ),
        'wiki': (
            'js/markup.js',
            'js/libs/django/urlify.js',
            'js/libs/django/prepopulate.js',
            'js/libs/jquery.cookie.js',
            'js/browserdetect.js',
            'js/libs/swfobject.js',
            'js/libs/jquery.selectbox-1.2.js',
            'js/libs/jquery.modal.js',
            'js/screencast.js',
            'js/wiki.js',
            'js/libs/jqueryui.min.js',
            'js/tags.js',
        ),
        'customercare': (
            'js/libs/jqueryui.min.js',
            'js/libs/jquery.NobleCount.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.bullseye-1.0.min.js',
            'js/customercare.js',
        ),
        'chat': (
            'js/chat.js',
        ),
    },
}

JAVA_BIN = '/usr/bin/java'

#
# Session cookies
SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

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

#
# Sphinx results tweaking
SEARCH_FORUM_MIN_AGE = 7  # age before which decay doesn't apply, in days
SEARCH_FORUM_HALF_LIFE = 14  # controls the decay rate, in days
SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 10

#
# Search default settings
# comma-separated tuple of included category IDs. Negative IDs are excluded.
SEARCH_DEFAULT_CATEGORIES = (10, 20,)
SEARCH_SUMMARY_LENGTH = 275
# because of markup cleanup, search summaries lengths vary quite a bit
# so we extract longer excerpts and perform truncation to the length above
SEARCH_SUMMARY_LENGTH_MULTIPLIER = 1.3

#
# The length for which we would like the user to cache search forms and
# results, in minutes.
SEARCH_CACHE_PERIOD = 15

# Maximum length of the filename. Forms should use this and raise
# ValidationError if the length is exceeded.
# @see http://code.djangoproject.com/ticket/9893
# Columns are 250 but this leaves 50 chars for the upload_to prefix
MAX_FILENAME_LENGTH = 200
MAX_FILEPATH_LENGTH = 250

# Auth and permissions related constants
# TODO: Once we can log in through Kitsune, change this.
LOGIN_URL = '/tiki-login.php'
LOGOUT_URL = '/tiki-logout.php'
REGISTER_URL = '/tiki-register.php'
WIKI_CREATE_URL = '/tiki-editpage.php?page=%s'
WIKI_EDIT_URL = '/tiki-editpage.php?page=%s'
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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


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
BROKER_USER = 'kitsune'
BROKER_PASSWORD = 'kitsune'
BROKER_VHOST = 'kitsune'
CELERY_RESULT_BACKEND = 'amqp'
CELERY_IGNORE_RESULT = True
CELERY_ALWAYS_EAGER = True  # For tests. Set to False for use.

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

# Customare care tweet collection settings
CC_MAX_TWEETS = 500 # Max. no. of tweets in DB
CC_TWEETS_PERPAGE = 100 # How many tweets to collect in one go. Max: 100.

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''

NOTIFICATIONS_FROM_ADDRESS = 'notifications@support.mozilla.com'

# URL of the chat server.
CHAT_SERVER = 'https://chat-support.mozilla.com:9091'
CHAT_CACHE_KEY = 'sumo-chat-queue-status'
