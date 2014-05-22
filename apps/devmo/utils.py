import time
import logging
import random
from django.core.cache import get_cache


class MemcacheLockException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class MemcacheLock(object):
    key = 'render-stale-documents-lock'

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
