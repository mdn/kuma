from __future__ import absolute_import

import imp
import importlib
import warnings

from celery import signals
from celery.loaders.base import BaseLoader
from celery.datastructures import DictAttribute

from django import db
from django.conf import settings
from django.core import cache
from django.core.mail import mail_admins

from .utils import DATABASE_ERRORS, now

_RACE_PROTECTION = False


class DjangoLoader(BaseLoader):
    """The Django loader."""
    _db_reuse = 0

    override_backends = {
            "database": "djcelery.backends.database.DatabaseBackend",
            "cache": "djcelery.backends.cache.CacheBackend"}

    def __init__(self, *args, **kwargs):
        super(DjangoLoader, self).__init__(*args, **kwargs)
        self._install_signal_handlers()

    def _install_signal_handlers(self):
        # Need to close any open database connection after
        # any embedded celerybeat process forks.
        signals.beat_embedded_init.connect(self.close_database)

    def now(self, **kwargs):
        return now()

    def read_configuration(self):
        """Load configuration from Django settings."""
        self.configured = True
        # Default backend needs to be the database backend for backward
        # compatibility.
        backend = getattr(settings, "CELERY_RESULT_BACKEND", None) or \
                    getattr(settings, "CELERY_BACKEND", None)
        if not backend:
            settings.CELERY_RESULT_BACKEND = "database"
        return DictAttribute(settings)

    def _close_database(self):
        try:
            funs = [conn.close for conn in db.connections]
        except AttributeError:
            funs = [db.close_connection]  # pre multidb

        for close in funs:
            try:
                close()
            except DATABASE_ERRORS, exc:
                if "closed" not in str(exc):
                    raise

    def close_database(self, **kwargs):
        db_reuse_max = self.conf.get("CELERY_DB_REUSE_MAX", None)
        if not db_reuse_max:
            return self._close_database()
        if self._db_reuse >= db_reuse_max * 2:
            self._db_reuse = 0
            self._close_database()
        self._db_reuse += 1

    def close_cache(self):
        try:
            cache.cache.close()
        except (TypeError, AttributeError):
            pass

    def on_process_cleanup(self):
        """Does everything necessary for Django to work in a long-living,
        multiprocessing environment.

        """
        # See http://groups.google.com/group/django-users/
        #            browse_thread/thread/78200863d0c07c6d/
        self.close_database()
        self.close_cache()

    def on_task_init(self, task_id, task):
        """Called before every task."""
        try:
            is_eager = task.request.is_eager
        except AttributeError:
            is_eager = False
        if not is_eager:
            self.close_database()

    def on_worker_init(self):
        """Called when the worker starts.

        Automatically discovers any ``tasks.py`` files in the applications
        listed in ``INSTALLED_APPS``.

        """

        if settings.DEBUG:
            warnings.warn("Using settings.DEBUG leads to a memory leak, never "
                          "use this setting in production environments!")
        self.import_default_modules()

        self.close_database()
        self.close_cache()

    def import_default_modules(self):
        super(DjangoLoader, self).import_default_modules()
        self.autodiscover()

    def autodiscover(self):
        self.task_modules.update(mod.__name__ for mod in autodiscover() or ())

    def on_worker_process_init(self):
        # the parent process may have established these,
        # so need to close them.
        self.close_database()
        self.close_cache()

    def mail_admins(self, subject, body, fail_silently=False, **kwargs):
        return mail_admins(subject, body, fail_silently=fail_silently)


def autodiscover():
    """Include tasks for all applications in ``INSTALLED_APPS``."""
    global _RACE_PROTECTION

    if _RACE_PROTECTION:
        return
    _RACE_PROTECTION = True
    try:
        return filter(None, [find_related_module(app, "tasks")
                                for app in settings.INSTALLED_APPS])
    finally:
        _RACE_PROTECTION = False


def find_related_module(app, related_name):
    """Given an application name and a module name, tries to find that
    module in the application."""

    try:
        app_path = importlib.import_module(app).__path__
    except AttributeError:
        return

    try:
        imp.find_module(related_name, app_path)
    except ImportError:
        return

    return importlib.import_module("%s.%s" % (app, related_name))
