import os

DEFAULT_CHARSET = 'utf-8'

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(os.path.dirname(__file__), 'threadedcomments_test.db')

ROOT_URLCONF = 'threadedcomments.urls'

GRAVATAR_DEFAULT_IMG = 'http://site.gravatar.com/images/common/top/logo.gif'

SITE_ID = 1

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'threadedcomments',
)
