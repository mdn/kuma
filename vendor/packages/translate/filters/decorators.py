#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

"""Decorators to categorize pofilter checks."""

from functools import wraps


#: Quality checks' failure categories
class Category(object):
    CRITICAL = 100
    FUNCTIONAL = 60
    COSMETIC = 30
    EXTRACTION = 10
    NO_CATEGORY = 0


def critical(f):

    @wraps(f)
    def critical_f(self, *args, **kwargs):
        if f.__name__ not in self.__class__.categories:
            self.__class__.categories[f.__name__] = Category.CRITICAL

        return f(self, *args, **kwargs)

    return critical_f


def functional(f):

    @wraps(f)
    def functional_f(self, *args, **kwargs):
        if f.__name__ not in self.__class__.categories:
            self.__class__.categories[f.__name__] = Category.FUNCTIONAL

        return f(self, *args, **kwargs)

    return functional_f


def cosmetic(f):

    @wraps(f)
    def cosmetic_f(self, *args, **kwargs):
        if f.__name__ not in self.__class__.categories:
            self.__class__.categories[f.__name__] = Category.COSMETIC

        return f(self, *args, **kwargs)

    return cosmetic_f


def extraction(f):

    @wraps(f)
    def extraction_f(self, *args, **kwargs):
        if f.__name__ not in self.__class__.categories:
            self.__class__.categories[f.__name__] = Category.EXTRACTION

        return f(self, *args, **kwargs)

    return extraction_f
