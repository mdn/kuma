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

"""Supports a hybrid Unicode string that knows which encoding is preferable, 
and uses this when converting to a string."""

class autoencode(unicode):
    def __new__(newtype, string=u"", encoding=None, errors=None):
        if isinstance(string, unicode):
            if errors is None:
                newstring = unicode.__new__(newtype, string)
            else:
                newstring = unicode.__new__(newtype, string, errors=errors)
            if encoding is None and isinstance(string, autoencode):
                newstring.encoding = string.encoding
            else:
                newstring.encoding = encoding
        else:
            if errors is None and encoding is None:
                newstring = unicode.__new__(newtype, string)
            elif errors is None:
                try:
                    newstring = unicode.__new__(newtype, string, encoding)
                except LookupError, e:
                    raise ValueError(str(e))
            elif encoding is None:
                newstring = unicode.__new__(newtype, string, errors)
            else:
                newstring = unicode.__new__(newtype, string, encoding, errors)
            newstring.encoding = encoding
        return newstring

    def join(self, seq):
        return autoencode(super(autoencode, self).join(seq))

    def __str__(self):
        if self.encoding is None:
            return super(autoencode, self).__str__()
        else:
            return self.encode(self.encoding)

