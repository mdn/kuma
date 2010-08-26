import os
import sys

SETTINGS_DIR = os.path.realpath(
        os.path.join(os.path.dirname(__file__), os.path.sep.join(('..',)*2)))

sys.path.append(SETTINGS_DIR)

# manage adds /apps, /lib and /vendor to the Python path.
import manage

from django.conf import settings

s = settings.DATABASES['default']
MYSQL_PASS = s['PASSWORD']
MYSQL_USER = s['USER']
MYSQL_HOST = s.get('HOST', 'localhost')
MYSQL_NAME = s['NAME']

if MYSQL_HOST.endswith('.sock'):
    MYSQL_HOST = 'localhost'

if os.environ.get('DJANGO_ENVIRONMENT') == 'test':
    MYSQL_NAME = 'test_' + MYSQL_NAME

ROOT_PATH       = '/tmp/k'
CATALOG_PATH    = '/data'
LOG_PATH        = '/log'
ETC_PATH        = '/etc'

LISTEN_PORT     = 3381
LISTEN_SQL_HOST = '127.0.0.1'
LISTEN_SQL_PORT = 3382
AGE_DIVISOR = 86400
