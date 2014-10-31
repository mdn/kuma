from __future__ import absolute_import, unicode_literals

import inspect
import sys
import time

from django.conf import settings
from django.core import cache
from django.core.cache import cache as original_cache, get_cache as original_get_cache
from django.core.cache.backends.base import BaseCache
from django.dispatch import Signal
from django.template import Node
from django.utils.translation import ugettext_lazy as _, ungettext
try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from debug_toolbar.panels import Panel
from debug_toolbar.utils import (tidy_stacktrace, render_stacktrace,
                                 get_template_info, get_stack)
from debug_toolbar import settings as dt_settings


cache_called = Signal(providing_args=[
    "time_taken", "name", "return_value", "args", "kwargs", "trace"])


def send_signal(method):
    def wrapped(self, *args, **kwargs):
        t = time.time()
        value = method(self, *args, **kwargs)
        t = time.time() - t

        if dt_settings.CONFIG['ENABLE_STACKTRACES']:
            stacktrace = tidy_stacktrace(reversed(get_stack()))
        else:
            stacktrace = []

        template_info = None
        cur_frame = sys._getframe().f_back
        try:
            while cur_frame is not None:
                if cur_frame.f_code.co_name == 'render':
                    node = cur_frame.f_locals['self']
                    if isinstance(node, Node):
                        template_info = get_template_info(node.source)
                        break
                cur_frame = cur_frame.f_back
        except Exception:
            pass
        del cur_frame
        cache_called.send(sender=self.__class__, time_taken=t,
                          name=method.__name__, return_value=value,
                          args=args, kwargs=kwargs, trace=stacktrace,
                          template_info=template_info, backend=self.cache)
        return value
    return wrapped


class CacheStatTracker(BaseCache):
    """A small class used to track cache calls."""
    def __init__(self, cache):
        self.cache = cache

    def __repr__(self):
        return str("<CacheStatTracker for %s>") % repr(self.cache)

    def _get_func_info(self):
        frame = sys._getframe(3)
        info = inspect.getframeinfo(frame)
        return (info[0], info[1], info[2], info[3])

    def __contains__(self, key):
        return self.cache.__contains__(key)

    def __getattr__(self, name):
        return getattr(self.cache, name)

    @send_signal
    def add(self, *args, **kwargs):
        return self.cache.add(*args, **kwargs)

    @send_signal
    def get(self, *args, **kwargs):
        return self.cache.get(*args, **kwargs)

    @send_signal
    def set(self, *args, **kwargs):
        return self.cache.set(*args, **kwargs)

    @send_signal
    def delete(self, *args, **kwargs):
        return self.cache.delete(*args, **kwargs)

    @send_signal
    def has_key(self, *args, **kwargs):
        return self.cache.has_key(*args, **kwargs)

    @send_signal
    def incr(self, *args, **kwargs):
        return self.cache.incr(*args, **kwargs)

    @send_signal
    def decr(self, *args, **kwargs):
        return self.cache.decr(*args, **kwargs)

    @send_signal
    def get_many(self, *args, **kwargs):
        return self.cache.get_many(*args, **kwargs)

    @send_signal
    def set_many(self, *args, **kwargs):
        self.cache.set_many(*args, **kwargs)

    @send_signal
    def delete_many(self, *args, **kwargs):
        self.cache.delete_many(*args, **kwargs)

    @send_signal
    def incr_version(self, *args, **kwargs):
        return self.cache.incr_version(*args, **kwargs)

    @send_signal
    def decr_version(self, *args, **kwargs):
        return self.cache.decr_version(*args, **kwargs)


def get_cache(*args, **kwargs):
    return CacheStatTracker(original_get_cache(*args, **kwargs))


class CachePanel(Panel):
    """
    Panel that displays the cache statistics.
    """
    template = 'debug_toolbar/panels/cache.html'

    def __init__(self, *args, **kwargs):
        super(CachePanel, self).__init__(*args, **kwargs)
        self.total_time = 0
        self.hits = 0
        self.misses = 0
        self.calls = []
        self.counts = OrderedDict((
            ('add', 0),
            ('get', 0),
            ('set', 0),
            ('delete', 0),
            ('get_many', 0),
            ('set_many', 0),
            ('delete_many', 0),
            ('has_key', 0),
            ('incr', 0),
            ('decr', 0),
            ('incr_version', 0),
            ('decr_version', 0),
        ))
        cache_called.connect(self._store_call_info)

    def _store_call_info(self, sender, name=None, time_taken=0,
                         return_value=None, args=None, kwargs=None,
                         trace=None, template_info=None, backend=None, **kw):
        if name == 'get':
            if return_value is None:
                self.misses += 1
            else:
                self.hits += 1
        elif name == 'get_many':
            for key, value in return_value.items():
                if value is None:
                    self.misses += 1
                else:
                    self.hits += 1
        self.total_time += time_taken * 1000
        self.counts[name] += 1
        self.calls.append({
            'time': time_taken,
            'name': name,
            'args': args,
            'kwargs': kwargs,
            'trace': render_stacktrace(trace),
            'template_info': template_info,
            'backend': backend
        })

    # Implement the Panel API

    nav_title = _("Cache")

    @property
    def nav_subtitle(self):
        cache_calls = len(self.calls)
        return ungettext("%(cache_calls)d call in %(time).2fms",
                         "%(cache_calls)d calls in %(time).2fms",
                         cache_calls) % {'cache_calls': cache_calls,
                                         'time': self.total_time}

    @property
    def title(self):
        count = len(getattr(settings, 'CACHES', ['default']))
        return ungettext("Cache calls from %(count)d backend",
                         "Cache calls from %(count)d backends",
                         count) % dict(count=count)

    def enable_instrumentation(self):
        # This isn't thread-safe because cache connections aren't thread-local
        # in Django, unlike database connections.
        cache.cache = CacheStatTracker(original_cache)
        cache.get_cache = get_cache

    def disable_instrumentation(self):
        cache.cache = original_cache
        cache.get_cache = original_get_cache

    def process_response(self, request, response):
        self.record_stats({
            'total_calls': len(self.calls),
            'calls': self.calls,
            'total_time': self.total_time,
            'hits': self.hits,
            'misses': self.misses,
            'counts': self.counts,
        })
