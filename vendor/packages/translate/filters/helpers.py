#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
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

"""a set of helper functions for filters..."""

import operator


def countmatch(str1, str2, countstr):
    """checks whether countstr occurs the same number of times in str1 and str2"""
    return str1.count(countstr) == str2.count(countstr)


def funcmatch(str1, str2, func, *args):
    """returns whether the result of func is the same for str1 and str2"""
    return func(str1, *args) == func(str2, *args)


def countsmatch(str1, str2, countlist):
    """checks whether each element in countlist occurs the same number of times in str1 and str2"""
    return reduce(operator.and_, [countmatch(str1, str2, countstr) for countstr in countlist], True)


def funcsmatch(str1, str2, funclist):
    """checks whether the results of each func in funclist match for str1 and str2"""
    return reduce(operator.and_, [funcmatch(str1, str2, funcstr) for funcstr in funclist], True)


def filtercount(str1, func):
    """returns the number of characters in str1 that pass func"""
    return len(filter(func, str1))


def filtertestmethod(testmethod, strfilter):
    """returns a version of the testmethod that operates on filtered strings using strfilter"""

    def filteredmethod(str1, str2):
        return testmethod(strfilter(str1), strfilter(str2))
    filteredmethod.__doc__ = testmethod.__doc__
    filteredmethod.name = getattr(testmethod, 'name', testmethod.__name__)
    return filteredmethod


def multifilter(str1, strfilters, *args):
    """passes str1 through a list of filters"""
    for strfilter in strfilters:
        str1 = strfilter(str1, *args)
    return str1


def multifiltertestmethod(testmethod, strfilters):
    """returns a version of the testmethod that operates on filtered strings using strfilter"""

    def filteredmethod(str1, str2):
        return testmethod(multifilter(str1, strfilters), multifilter(str2, strfilters))
    filteredmethod.__doc__ = testmethod.__doc__
    filteredmethod.name = getattr(testmethod, 'name', testmethod.__name__)
    return filteredmethod
