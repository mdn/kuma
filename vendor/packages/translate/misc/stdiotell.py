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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""A wrapper for sys.stdout etc that provides tell() for current position"""


class StdIOWrapper:

    def __init__(self, stream):
        self.stream = stream
        self.pos = 0
        self.closed = 0

    def __getattr__(self, attrname, default=None):
        return getattr(self.stream, attrname, default)

    def close(self):
        if not self.closed:
            self.closed = 1
            self.stream.close()

    def seek(self, pos, mode=0):
        raise ValueError("I/O operation on closed file")

    def tell(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.pos

    def write(self, s):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self.stream.write(s)
        self.pos += len(s)

    def writelines(self, lines):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self.stream.writelines(lines)
        self.pos += len("".join(lines))
