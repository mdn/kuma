# pylint: disable-msg=E0601,W0622,W0611
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
"""Wrappers around some builtins introduced in python 2.3, 2.4 and
2.5, making them available in for earlier versions of python.




"""
from __future__ import generators
__docformat__ = "restructuredtext en"

import os
from warnings import warn

import __builtin__

try:
    set = set
    frozenset = frozenset
except NameError:
    try:
        from sets import Set as set, ImmutableSet as frozenset
    except ImportError:
        class _baseset(object):
            def __init__(self, values=()):
                self._data = {}
                warn("This implementation of Set is not complete !",
                     stacklevel=2)
                for v in values:
                    self._data[v] = 1

            def __or__(self, other):
                result = self.__class__(self._data.keys())
                for val in other:
                    result.add(val)
                return result
            __add__ = __or__

            def __and__(self, other):
                result = self.__class__()
                for val in other:
                    if val in self._data:
                        result.add(val)
                return result

            def __sub__(self, other):
                result = self.__class__(self._data.keys())
                for val in other:
                    if val in self._data:
                        result.remove(val)
                return result

            def __cmp__(self, other):
                keys = self._data.keys()
                okeys = other._data.keys()
                keys.sort()
                okeys.sort()
                return cmp(keys, okeys)

            def __len__(self):
                return len(self._data)

            def __repr__(self):
                elements = self._data.keys()
                return 'lcc.%s(%r)' % (self.__class__.__name__, elements)
            __str__ = __repr__

            def __iter__(self):
                return iter(self._data)

        class frozenset(_baseset):
            """immutable set (can be set in dictionaries)"""
            def __init__(self, values=()):
                super(frozenset, self).__init__(values)
                self._hashcode = None

            def _compute_hash(self):
                """taken from python stdlib (sets.py)"""
                # Calculate hash code for a set by xor'ing the hash codes of
                # the elements.  This ensures that the hash code does not depend
                # on the order in which elements are added to the set.  This is
                # not called __hash__ because a BaseSet should not be hashable;
                # only an ImmutableSet is hashable.
                result = 0
                for elt in self:
                    result ^= hash(elt)
                return result

            def __hash__(self):
                """taken from python stdlib (sets.py)"""
                if self._hashcode is None:
                    self._hashcode = self._compute_hash()
                return self._hashcode


        class set(_baseset):
            """mutable set"""
            def add(self, value):
                self._data[value] = 1

            def remove(self, element):
                """removes <element> from set"""
                del self._data[element]

            def pop(self):
                """pops an arbitrary element from set"""
                return self._data.popitem()[0]

            def __hash__(self):
                """mutable set cannot be hashed."""
                raise TypeError("set objects are not hashable")

        del _baseset # don't explicitly provide this class

try:
    from itertools import izip, chain, imap
except ImportError:
    # from itertools documentation ###
    def izip(*iterables):
        iterables = map(iter, iterables)
        while iterables:
            result = [i.next() for i in iterables]
            yield tuple(result)

    def chain(*iterables):
        for it in iterables:
            for element in it:
                yield element

    def imap(function, *iterables):
        iterables = map(iter, iterables)
        while True:
            args = [i.next() for i in iterables]
            if function is None:
                yield tuple(args)
            else:
                yield function(*args)
try:
    sum = sum
    enumerate = enumerate
except NameError:
    # define the sum and enumerate functions (builtins introduced in py 2.3)
    import operator
    def sum(seq, start=0):
        """Returns the sum of all elements in the sequence"""
        return reduce(operator.add, seq, start)

    def enumerate(iterable):
        """emulates the python2.3 enumerate() function"""
        i = 0
        for val in iterable:
            yield i, val
            i += 1
        #return zip(range(len(iterable)), iterable)
try:
    sorted = sorted
    reversed = reversed
except NameError:

    def sorted(iterable, cmp=None, key=None, reverse=False):
        original = list(iterable)
        if key:
            l2 = [(key(elt), index) for index, elt in enumerate(original)]
        else:
            l2 = original
        l2.sort(cmp)
        if reverse:
            l2.reverse()
        if key:
            return [original[index] for elt, index in l2]
        return l2

    def reversed(l):
        l2 = list(l)
        l2.reverse()
        return l2

try: #
    max = max
    max(("ab","cde"),key=len)
except TypeError:
    def max( *args, **kargs):
        if len(args) == 0:
            raise TypeError("max expected at least 1 arguments, got 0")
        key= kargs.pop("key", None)
        #default implementation
        if key is None:
            return __builtin__.max(*args,**kargs)

        for karg in kargs:
            raise TypeError("unexpected keyword argument %s for function max") % karg

        if len(args) == 1:
            items = iter(args[0])
        else:
            items = iter(args)

        try:
            best_item = items.next()
            best_value = key(best_item)
        except StopIteration:
            raise ValueError("max() arg is an empty sequence")

        for item in items:
            value = key(item)
            if value > best_value:
                best_item = item
                best_value = value

        return best_item


# Python2.5 builtins
try:
    any = any
    all = all
except NameError:
    def any(iterable):
        """any(iterable) -> bool

        Return True if bool(x) is True for any x in the iterable.
        """
        for elt in iterable:
            if elt:
                return True
        return False

    def all(iterable):
        """all(iterable) -> bool

        Return True if bool(x) is True for all values x in the iterable.
        """
        for elt in iterable:
            if not elt:
                return False
        return True


# Python2.5 subprocess added functions and exceptions
try:
    from subprocess import Popen
except ImportError:
    # gae or python < 2.3

    class CalledProcessError(Exception):
        """This exception is raised when a process run by check_call() returns
        a non-zero exit status.  The exit status will be stored in the
        returncode attribute."""
        def __init__(self, returncode, cmd):
            self.returncode = returncode
            self.cmd = cmd
        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (self.cmd,
    self.returncode)

    def call(*popenargs, **kwargs):
        """Run command with arguments.  Wait for command to complete, then
        return the returncode attribute.

        The arguments are the same as for the Popen constructor.  Example:

        retcode = call(["ls", "-l"])
        """
        # workaround: subprocess.Popen(cmd, stdout=sys.stdout) fails
        # see http://bugs.python.org/issue1531862
        if "stdout" in kwargs:
            fileno = kwargs.get("stdout").fileno()
            del kwargs['stdout']
            return Popen(stdout=os.dup(fileno), *popenargs, **kwargs).wait()
        return Popen(*popenargs, **kwargs).wait()

    def check_call(*popenargs, **kwargs):
        """Run command with arguments.  Wait for command to complete.  If
        the exit code was zero then return, otherwise raise
        CalledProcessError.  The CalledProcessError object will have the
        return code in the returncode attribute.

        The arguments are the same as for the Popen constructor.  Example:

        check_call(["ls", "-l"])
        """
        retcode = call(*popenargs, **kwargs)
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        if retcode:
            raise CalledProcessError(retcode, cmd)
        return retcode

try:
    from os.path import relpath
except ImportError: # python < 2.6
    from os.path import curdir, abspath, sep, commonprefix, pardir, join
    def relpath(path, start=curdir):
        """Return a relative version of a path"""

        if not path:
            raise ValueError("no path specified")

        start_list = abspath(start).split(sep)
        path_list = abspath(path).split(sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)


