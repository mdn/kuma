#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Implements a case-insensitive (on keys) dictionary and order-sensitive dictionary"""

# Copyright 2002, 2003 St James Software
# 
# This file is part of translate.
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

def generalupper(str):
    """this uses the object's upper method - works with string and unicode"""
    if str is None: return str
    return str.upper()

class cidict(dict):
    def __init__(self, fromdict = None):
        """constructs the cidict, optionally using another dict to do so"""
        if fromdict is not None:
            self.update(fromdict)

    def __getitem__(self, key):
        if type(key) != str and type(key) != unicode:
            raise TypeError, "cidict can only have str or unicode as key (got %r)" % type(key)
        for akey in self.iterkeys():
            if akey.lower() == key.lower():
                return dict.__getitem__(self, akey)
        raise IndexError

    def __setitem__(self, key, value):
        if type(key) != str and type(key) != unicode:
            raise TypeError, "cidict can only have str or unicode as key (got %r)" % type(key)
        for akey in self.iterkeys():
            if akey.lower() == key.lower():
                return dict.__setitem__(self, akey, value)
        return dict.__setitem__(self, key, value)

    def update(self, updatedict):
        """D.update(E) -> None.  Update D from E: for k in E.keys(): D[k] = E[k]"""
        for key, value in updatedict.iteritems():
            self[key] = value

    def __delitem__(self, key):
        if type(key) != str and type(key) != unicode:
            raise TypeError, "cidict can only have str or unicode as key (got %r)" % type(key)
        for akey in self.iterkeys():
            if akey.lower() == key.lower():
                return dict.__delitem__(self, akey)
        raise IndexError

    def __contains__(self, key):
        if type(key) != str and type(key) != unicode:
            raise TypeError, "cidict can only have str or unicode as key (got %r)" % type(key)
        for akey in self.iterkeys():
            if akey.lower() == key.lower():
                return 1
        return 0

    def has_key(self, key):
        return self.__contains__(key)

    def get(self, key, default=None):
        if self.has_key(key):
            return self[key]
        else:
            return default

class ordereddict(dict):
    """a dictionary which remembers its keys in the order in which they were given"""
    def __init__(self, *args):
        if len(args) == 0:
            super(ordereddict, self).__init__()
            self.order = []
        elif len(args) > 1:
            raise TypeError("ordereddict() takes at most 1 argument (%d given)" % len(args))
        else:
            initarg = args[0]
            apply(super(ordereddict, self).__init__, args)
            if hasattr(initarg, "keys"):
                self.order = initarg.keys()
            else:
                # danger: could have duplicate keys...
                self.order = []
                checkduplicates = {}
                for key, value in initarg:
                    if not key in checkduplicates:
                        self.order.append(key)
                        checkduplicates[key] = None

    def __setitem__(self, key, value):
        alreadypresent = key in self
        result = dict.__setitem__(self, key, value)
        if not alreadypresent: self.order.append(key)
        return result

    def update(self, updatedict):
        """D.update(E) -> None.  Update D from E: for k in E.keys(): D[k] = E[k]"""
        for key, value in updatedict.iteritems():
            self[key] = value

    def __delitem__(self, key):
        alreadypresent = key in self
        result = dict.__delitem__(self, key)
        if alreadypresent: del self.order[self.order.index(key)]
        return result

    def copy(self):
        """D.copy() -> a shallow copy of D"""
        thecopy = ordereddict(super(ordereddict, self).copy())
        thecopy.order = self.order[:]
        return thecopy

    def items(self):
        """D.items() -> list of D's (key, value) pairs, as 2-tuples"""
        return [(key, self[key]) for key in self.order]

    def iteritems(self):
        """D.iteritems() -> an iterator over the (key, value) items of D"""
        for key in self.order:
            yield (key, self[key])

    def iterkeys(self):
        """D.iterkeys() -> an iterator over the keys of D"""
        for key in self.order:
            yield key

    __iter__ = iterkeys

    def itervalues(self):
        """D.itervalues() -> an iterator over the values of D"""
        for key in self.order:
            yield self[key]

    def keys(self):
        """D.keys() -> list of D's keys"""
        return self.order[:]

    def popitem(self):
        """D.popitem() -> (k, v), remove and return some (key, value) pair as a 2-tuple; but raise KeyError if D is empty"""
        if len(self.order) == 0:
            raise KeyError("popitem(): ordered dictionary is empty")
        k = self.order.pop()
        v = self[k]
        del self[k]
        return (k,v)

    def pop(self, key):
        """remove entry from dict and internal list"""
        value = super(ordereddict, self).pop(key)
        del self.order[self.order.index(key)]
        return value
