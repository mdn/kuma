# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""A few useful function/method decorators.




"""
__docformat__ = "restructuredtext en"

from types import MethodType
from time import clock, time
import sys, re

# XXX rewrite so we can use the decorator syntax when keyarg has to be specified

def cached(callableobj, keyarg=None):
    """Simple decorator to cache result of method call."""
    if callableobj.func_code.co_argcount == 1 or keyarg == 0:

        def cache_wrapper1(self, *args):
            cache = '_%s_cache_' % callableobj.__name__
            #print 'cache1?', cache
            try:
                return self.__dict__[cache]
            except KeyError:
                #print 'miss'
                value = callableobj(self, *args)
                setattr(self, cache, value)
                return value
        cache_wrapper1.__doc__ = callableobj.__doc__
        return cache_wrapper1

    elif keyarg:

        def cache_wrapper2(self, *args, **kwargs):
            cache = '_%s_cache_' % callableobj.__name__
            key = args[keyarg-1]
            #print 'cache2?', cache, self, key
            try:
                _cache = self.__dict__[cache]
            except KeyError:
                #print 'init'
                _cache = {}
                setattr(self, cache, _cache)
            try:
                return _cache[key]
            except KeyError:
                #print 'miss', self, cache, key
                _cache[key] = callableobj(self, *args, **kwargs)
            return _cache[key]
        cache_wrapper2.__doc__ = callableobj.__doc__
        return cache_wrapper2

    def cache_wrapper3(self, *args):
        cache = '_%s_cache_' % callableobj.__name__
        #print 'cache3?', cache, self, args
        try:
            _cache = self.__dict__[cache]
        except KeyError:
            #print 'init'
            _cache = {}
            setattr(self, cache, _cache)
        try:
            return _cache[args]
        except KeyError:
            #print 'miss'
            _cache[args] = callableobj(self, *args)
        return _cache[args]
    cache_wrapper3.__doc__ = callableobj.__doc__
    return cache_wrapper3

def clear_cache(obj, funcname):
    """Function to clear a cache handled by the cached decorator."""
    try:
        del obj.__dict__['_%s_cache_' % funcname]
    except KeyError:
        pass

def copy_cache(obj, funcname, cacheobj):
    """Copy cache for <funcname> from cacheobj to obj."""
    cache = '_%s_cache_' % funcname
    try:
        setattr(obj, cache, cacheobj.__dict__[cache])
    except KeyError:
        pass

class wproperty(object):
    """Simple descriptor expecting to take a modifier function as first argument
    and looking for a _<function name> to retrieve the attribute.
    """
    def __init__(self, setfunc):
        self.setfunc = setfunc
        self.attrname = '_%s' % setfunc.__name__

    def __set__(self, obj, value):
        self.setfunc(obj, value)

    def __get__(self, obj, cls):
        assert obj is not None
        return getattr(obj, self.attrname)


class classproperty(object):
    """this is a simple property-like class but for class attributes.
    """
    def __init__(self, get):
        self.get = get
    def __get__(self, inst, cls):
        return self.get(cls)


class iclassmethod(object):
    '''Descriptor for method which should be available as class method if called
    on the class or instance method if called on an instance.
    '''
    def __init__(self, func):
        self.func = func
    def __get__(self, instance, objtype):
        if instance is None:
            return MethodType(self.func, objtype, objtype.__class__)
        return MethodType(self.func, instance, objtype)
    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")


def timed(f):
    def wrap(*args, **kwargs):
        t = time()
        c = clock()
        res = f(*args, **kwargs)
        print '%s clock: %.9f / time: %.9f' % (f.__name__,
                                               clock() - c, time() - t)
        return res
    return wrap


def locked(acquire, release):
    """Decorator taking two methods to acquire/release a lock as argument,
    returning a decorator function which will call the inner method after
    having called acquire(self) et will call release(self) afterwards.
    """
    def decorator(f):
        def wrapper(self, *args, **kwargs):
            acquire(self)
            try:
                return f(self, *args, **kwargs)
            finally:
                release(self)
        return wrapper
    return decorator


def monkeypatch(klass, methodname=None):
    """Decorator extending class with the decorated function
    >>> class A:
    ...     pass
    >>> @monkeypatch(A)
    ... def meth(self):
    ...     return 12
    ...
    >>> a = A()
    >>> a.meth()
    12
    >>> @monkeypatch(A, 'foo')
    ... def meth(self):
    ...     return 12
    ...
    >>> a.foo()
    12
    """
    def decorator(func):
        setattr(klass, methodname or func.__name__, func)
        return func
    return decorator
