import HTMLParser
import time
import logging
import random
import functools
import os
import tempfile

import commonware.log
import lockfile
from polib import pofile

from django.conf import settings
from django.core.cache import get_cache
from django.shortcuts import _get_queryset


log = commonware.log.getLogger('mdn.devmo.utils')
htmlparser = HTMLParser.HTMLParser()


def strings_are_translated(strings, locale):
    # http://stackoverflow.com/a/24339946/571420
    pofile_path = os.path.join(settings.ROOT, 'locale', locale, 'LC_MESSAGES',
                               'messages.po')
    try:
        po = pofile(pofile_path)
    except IOError:  # in case the file doesn't exist or couldn't be parsed
        return False
    all_strings_translated = True
    for string in strings:
        if not any(e for e in po if e.msgid == string and
                   (e.translated() and 'fuzzy' not in e.flags)
                   and not e.obsolete):
            all_strings_translated = False
    return all_strings_translated


def file_lock(prefix):
    """
    Decorator that only allows one instance of the same command to run
    at a time.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            name = '_'.join((prefix, f.__name__) + args)
            file = os.path.join(tempfile.gettempdir(), name)
            lock = lockfile.FileLock(file)
            try:
                # Try to acquire the lock without blocking.
                lock.acquire(0)
            except lockfile.LockError:
                log.warning('Aborting %s; lock acquisition failed.' % name)
                return 0
            else:
                # We have the lock, call the function.
                try:
                    return f(self, *args, **kwargs)
                finally:
                    lock.release()
        return wrapper
    return decorator


def generate_filename_and_delete_previous(ffile, name, before_delete=None):
    """Generate a new filename for a file upload field; delete the previously
    uploaded file."""

    new_filename = ffile.field.generate_filename(ffile.instance, name)

    try:
        # HACK: Speculatively re-fetching the original object makes me feel
        # wasteful and dirty. But, I can't think of another way to get
        # to the original field's value. Should be cached, though.
        # see also - http://code.djangoproject.com/ticket/11663#comment:10
        orig_instance = ffile.instance.__class__.objects.get(
            id=ffile.instance.id
        )
        orig_field_file = getattr(orig_instance, ffile.field.name)
        orig_filename = orig_field_file.name

        if orig_filename and new_filename != orig_filename:
            if before_delete:
                before_delete(orig_field_file)
            orig_field_file.delete()
    except ffile.instance.__class__.DoesNotExist:
        pass

    return new_filename


class MemcacheLockException(Exception):
    pass


class MemcacheLock(object):
    def __init__(self, key, attempts=1, expires=60 * 60 * 3):
        self.key = 'lock_%s' % key
        self.attempts = attempts
        self.expires = expires
        self.cache = get_cache('memcache')

    @property
    def acquired(self):
        return bool(self.cache.get(self.key))

    def acquire(self):
        cache = get_cache('memcache')
        for i in xrange(0, self.attempts):
            stored = cache.add(self.key, 1, self.expires)
            if stored:
                return True
            if i != self.attempts - 1:
                sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                logging.debug('Sleeping for %s while trying to acquire key %s',
                              sleep_time, self.key)
                time.sleep(sleep_time)
        raise MemcacheLockException('Could not acquire lock for %s' % self.key)

    def release(self):
        self.cache.delete(self.key)


def entity_decode(str):
    """Turn HTML entities in a string into unicode."""
    return htmlparser.unescape(str)


def get_object_or_none(klass, *args, **kwargs):
    """
    A tool like Django's get_object_or_404 but returns None in case
    of a DoesNotExist exception.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None
