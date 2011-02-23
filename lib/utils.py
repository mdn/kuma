import functools
import HTMLParser
import os
import re
import tempfile

import commonware.log
import lockfile


log = commonware.log.getLogger('basket')
htmlparser = HTMLParser.HTMLParser()


def locked(prefix):
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


def cached_property(*args, **kw):
    # Handles invocation as a direct decorator or
    # with intermediate keyword arguments.
    if args: # @cached_property
        return CachedProperty(args[0])
    else: # @cached_property(name=..., writable=...)
        return lambda f: CachedProperty(f, **kw)


class CachedProperty(object):
    """A decorator that converts a function into a lazy property. The
function wrapped is called the first time to retrieve the result
and than that calculated result is used the next time you access
the value::

class Foo(object):

@cached_property
def foo(self):
# calculate something important here
return 42

Lifted from werkzeug.
"""

    def __init__(self, func, name=None, doc=None, writable=False):
        self.func = func
        self.writable = writable
        self.__name__ = name or func.__name__
        self.__doc__ = doc or func.__doc__

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        _missing = object()
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value

    def __set__(self, obj, value):
        if not self.writable:
            raise TypeError('read only attribute')
        obj.__dict__[self.__name__] = value


def entity_decode(str):
    """Turn HTML entities in a string into unicode."""
    return htmlparser.unescape(str)

import jingo

class JingoTemplateLoaderWrapper():

    def __init__(self, template):
        self.template = template

    def render(self, context):
        context_dict = {}
        for d in context.dicts:
            context_dict.update(d)
        return self.template.render(context_dict)

class JingoTemplateLoader():
    """Quick & dirty adaptor to load jinja2 templates via jingo"""
    is_usable = True

    def get_template(self, template_name, template_dirs=None):
        if not jingo._helpers_loaded:
            jingo.load_helpers()
        template = jingo.env.get_template(template_name)
        return JingoTemplateLoaderWrapper(template)

