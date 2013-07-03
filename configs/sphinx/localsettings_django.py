# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

SETTINGS_DIR = os.path.realpath(
        os.path.join(os.path.dirname(__file__), os.path.sep.join(('..',) * 2)))

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

LISTEN_PORT     = settings.SPHINX_PORT
LISTEN_SQL_HOST = settings.SPHINX_HOST
LISTEN_SQL_PORT = settings.SPHINXQL_PORT

if os.environ.get('DJANGO_ENVIRONMENT') == 'test':
    MYSQL_NAME = 'test_' + MYSQL_NAME
    LISTEN_PORT = settings.TEST_SPHINX_PORT
    LISTEN_SQL_PORT = settings.TEST_SPHINXQL_PORT

ROOT_PATH       = settings.TEST_SPHINX_PATH
CATALOG_PATH    = '/data'
LOG_PATH        = '/log'
ETC_PATH        = '/etc'

AGE_DIVISOR = 86400
