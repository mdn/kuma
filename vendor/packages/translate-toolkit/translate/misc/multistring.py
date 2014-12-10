#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2006 Zuza Software Foundation
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

"""Supports a hybrid Unicode string that can also have a list of alternate strings in the strings attribute"""

from translate.misc import autoencode

class multistring(autoencode.autoencode):
    def __new__(newtype, string=u"", encoding=None, errors=None):
        if isinstance(string, list):
            if not string:
                raise ValueError("multistring must contain at least one string")
            mainstring = string[0]
            newstring = multistring.__new__(newtype, string[0], encoding, errors)
            newstring.strings = [newstring] + [autoencode.autoencode.__new__(autoencode.autoencode, altstring, encoding, errors) for altstring in string[1:]]
        else:
            newstring = autoencode.autoencode.__new__(newtype, string, encoding, errors)
            newstring.strings = [newstring]
        return newstring

    def __init__(self, *args, **kwargs):
        super(multistring, self).__init__()
        if not hasattr(self, "strings"):
            self.strings = []

    def __cmp__(self, otherstring):
        if isinstance(otherstring, multistring):
            parentcompare = cmp(autoencode.autoencode(self), otherstring)
            if parentcompare:
                return parentcompare
            else:
                return cmp(self.strings[1:], otherstring.strings[1:])
        elif isinstance(otherstring, autoencode.autoencode):
            return cmp(autoencode.autoencode(self), otherstring)
        elif isinstance(otherstring, unicode):
            return cmp(unicode(self), otherstring)
        elif isinstance(otherstring, str):
            return cmp(str(self), otherstring)
        elif isinstance(otherstring, list):
            return cmp(self, multistring(otherstring))
        else:
            return cmp(type(self), type(otherstring))

    def __ne__(self, otherstring):
        return self.__cmp__(otherstring) != 0

    def __eq__(self, otherstring):
        return self.__cmp__(otherstring) == 0

    def __repr__(self):
        parts = [autoencode.autoencode.__repr__(self)] + [repr(a) for a in self.strings[1:]]
        return "multistring([" + ",".join(parts) + "])"

    def replace(self, old, new, count=None):
        if count is None:
            newstr = multistring(super(multistring, self).replace(old, new), self.encoding)
        else:
            newstr = multistring(super(multistring, self).replace(old, new, count), self.encoding)
        for s in self.strings[1:]:
            if count is None:
                newstr.strings.append(s.replace(old, new))
            else:
                newstr.strings.append(s.replace(old, new, count))
        return newstr
