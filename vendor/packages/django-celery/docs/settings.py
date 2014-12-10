# Django settings for docs project.

# import source code dir
import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), os.pardir))

SITE_ID = 303
DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {"default": {"NAME": ":memory:",
                         "ENGINE": "django.db.backends.sqlite3",
                         "USER": '',
                         "PASSWORD": '',
                         "PORT": ''}}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'djcelery',
)
