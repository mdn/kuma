# Django settings for testproj project.

import warnings
warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')

import os
import sys
# import source code dir
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), os.pardir))

NO_NOSE = os.environ.get("DJCELERY_NO_NOSE", False)

SITE_ID = 300

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ROOT_URLCONF = "tests.urls"

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

if not NO_NOSE:
    TEST_RUNNER = "django_nose.run_tests"
here = os.path.abspath(os.path.dirname(__file__))
COVERAGE_EXCLUDE_MODULES = ("djcelery",
                            "djcelery.tests.*",
                            "djcelery.management.*",
                            "djcelery.contrib.*",
)

NOSE_ARGS = [os.path.join(here, os.pardir, "djcelery", "tests"),
            os.environ.get("NOSE_VERBOSE") and "--verbose" or "",
            "--cover3-package=djcelery",
            "--cover3-branch",
            "--cover3-exclude=%s" % ",".join(COVERAGE_EXCLUDE_MODULES)]

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_VHOST = "/"
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"

TT_HOST = "localhost"
TT_PORT = 1978

CELERY_DEFAULT_EXCHANGE = "testcelery"
CELERY_DEFAULT_ROUTING_KEY = "testcelery"
CELERY_DEFAULT_QUEUE = "testcelery"

CELERY_QUEUES = {"testcelery": {"binding_key": "testcelery"}}

MANAGERS = ADMINS

DATABASES = {"default": {"NAME": "djcelery-test-db",
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
    'someapp',
    'someappwotask',
)

if not NO_NOSE:
    INSTALLED_APPS = INSTALLED_APPS + ("django_nose", )

CELERY_SEND_TASK_ERROR_EMAILS = False

USE_TZ = True
