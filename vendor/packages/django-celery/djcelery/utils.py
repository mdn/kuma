# -- XXX This module must not use translation as that causes
# -- a recursive loader import!
from __future__ import absolute_import

from datetime import datetime

from django.conf import settings

# Database-related exceptions.
from django.db import DatabaseError
try:
    import MySQLdb as mysql
    _my_database_errors = (mysql.DatabaseError, )
except ImportError:
    _my_database_errors = ()      # noqa
try:
    import psycopg2 as pg
    _pg_database_errors = (pg.DatabaseError, )
except ImportError:
    _pg_database_errors = ()      # noqa
try:
    import sqlite3
    _lite_database_errors = (sqlite3.DatabaseError, )
except ImportError:
    _lite_database_errors = ()    # noqa
try:
    import cx_Oracle as oracle
    _oracle_database_errors = (oracle.DatabaseError, )
except ImportError:
    _oracle_database_errors = ()  # noqa

DATABASE_ERRORS = ((DatabaseError, ) +
                   _my_database_errors +
                   _pg_database_errors +
                   _lite_database_errors +
                   _oracle_database_errors)

try:
    from django.utils import timezone

    def make_aware(value):
        if getattr(settings, "USE_TZ", False):
            default_tz = timezone.get_default_timezone()
            value = timezone.make_aware(value, default_tz)
        return value

    def make_naive(value):
        if getattr(settings, "USE_TZ", False):
            default_tz = timezone.get_default_timezone()
            value = timezone.make_naive(value, default_tz)
        return value

    def now():
        return timezone.localtime(timezone.now())

except ImportError:
    now = datetime.now
    make_aware = make_naive = lambda x: x
