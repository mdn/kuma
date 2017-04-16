#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2006 Zuza Software Foundation
# 
# This file is part of translate.
# The file was copied from the Python 2.5 source.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# NB! IMPORTANT SEMANTIC DIFFERENCE WITH THE OFFICIAL contextlib.
# In Python 2.5+, if an exception is thrown in a 'with' statement
# which uses a generator-based context manager (that is, a
# context manager created by decorating a generator with
# @contextmanager), the exception will be propagated to the 
# generator via the .throw method of the generator.
#
# This does not exist in Python 2.4. Thus, we just naively finish
# off the context manager. This also means that generator-based
# context managers can't deal with exceptions, so be warned.

"""Utilities for with-statement contexts.  See PEP 343."""

import sys

__all__ = ["contextmanager", "nested", "closing"]

class GeneratorContextManager(object):
    """Helper for @contextmanager decorator."""

    def __init__(self, gen):
        self.gen = gen

    def __enter__(self):
        try:
            return self.gen.next()
        except StopIteration:
            raise RuntimeError("generator didn't yield")

    def __exit__(self, type, value, tb):
        if type is None:
            try:
                self.gen.next()
            except StopIteration:
                return
            else:
                raise RuntimeError("generator didn't stop")
        else:            
            if value is None:
                # Need to force instantiation so we can reliably
                # tell if we get the same exception back
                value = type()
            try:
                try:
                    self.gen.next()
                except StopIteration:
                    import traceback
                    traceback.print_exception(type, value, tb)
                    raise value
            except StopIteration, exc:
                # Suppress the exception *unless* it's the same exception that
                # was passed to throw().  This prevents a StopIteration
                # raised inside the "with" statement from being suppressed
                return exc is not value

def contextmanager(func):
    """@contextmanager decorator.

    Typical usage:

        @contextmanager
        def some_generator(<arguments>):
            <setup>
            try:
                yield <value>
            finally:
                <cleanup>

    This makes this:

        with some_generator(<arguments>) as <variable>:
            <body>

    equivalent to this:

        <setup>
        try:
            <variable> = <value>
            <body>
        finally:
            <cleanup>

    """
    def helper(*args, **kwds):
        return GeneratorContextManager(func(*args, **kwds))
    try:
        helper.__name__ = func.__name__
        helper.__doc__ = func.__doc__
        helper.__dict__ = func.__dict__
    except:
        pass
    return helper


@contextmanager
def nested(*managers):
    """Support multiple context managers in a single with-statement.

    Code like this:

        with nested(A, B, C) as (X, Y, Z):
            <body>

    is equivalent to this:

        with A as X:
            with B as Y:
                with C as Z:
                    <body>

    """
    exits = []
    vars = []
    exc = (None, None, None)
    # Lambdas are an easy way to create unique objects. We don't want
    # this to be None, since our answer might actually be None
    undefined = lambda: 42 
    result = undefined

    try:
        for mgr in managers:
            exit = mgr.__exit__
            enter = mgr.__enter__
            vars.append(enter())
            exits.append(exit)
        result = vars
    except:
        exc = sys.exc_info()

    # If nothing has gone wrong, then result contains our return value
    # and thus it is not equal to 'undefined'. Thus, yield the value.
    if result != undefined:
        yield result

    while exits:
        exit = exits.pop()
        try:
            if exit(*exc):
                exc = (None, None, None)
        except:
            exc = sys.exc_info()
    if exc != (None, None, None):
        # Don't rely on sys.exc_info() still containing
        # the right information. Another exception may
        # have been raised and caught by an exit method
        raise exc[0], exc[1], exc[2]

class closing(object):
    """Context to automatically close something at the end of a block.

    Code like this:

        with closing(<module>.open(<arguments>)) as f:
            <block>

    is equivalent to this:

        f = <module>.open(<arguments>)
        try:
            <block>
        finally:
            f.close()

    """
    def __init__(self, thing):
        self.thing = thing
    def __enter__(self):
        return self.thing
    def __exit__(self, *exc_info):
        self.thing.close()
