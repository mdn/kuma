#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""
Contains base placeable classes with names based on XLIFF placeables. See the
XLIFF standard for more information about what the names mean.
"""

from strelem import StringElem
from interfaces import *


__all__ = ['Bpt', 'Ept', 'Ph', 'It', 'G', 'Bx', 'Ex', 'X', 'Sub', 'to_base_placeables']


# Basic placeable types.
class Bpt(MaskingPlaceable, PairedDelimiter):
    has_content = True


class Ept(MaskingPlaceable, PairedDelimiter):
    has_content = True


class Ph(MaskingPlaceable):
    has_content = True
    istranslatable = False


class It(MaskingPlaceable, Delimiter):
    has_content = True


class G(ReplacementPlaceable):
    has_content = True


class Bx(ReplacementPlaceable, PairedDelimiter):
    has_content = False
    istranslatable = False

    def __init__(self, id=None, xid=None, **kwargs):
        # kwargs is ignored
        ReplacementPlaceable.__init__(self, id=id, xid=xid, **kwargs)


class Ex(ReplacementPlaceable, PairedDelimiter):
    has_content = False
    istranslatable = False

    def __init__(self, id=None, xid=None, **kwargs):
        # kwargs is ignored
        ReplacementPlaceable.__init__(self, id=id, xid=xid, **kwargs)


class X(ReplacementPlaceable, Delimiter):
    has_content = False
    iseditable = False
    isfragile = True
    istranslatable = False

    def __init__(self, id=None, xid=None, **kwargs):
        ReplacementPlaceable.__init__(self, id=id, xid=xid, **kwargs)


class Sub(SubflowPlaceable):
    has_content = True


def to_base_placeables(tree):
    if not isinstance(tree, StringElem):
        return tree

    base_class = [klass for klass in tree.__class__.__bases__ \
                  if klass in [Bpt, Ept, Ph, It, G, Bx, Ex, X, Sub]]

    if not base_class:
        base_class = tree.__class__
    else:
        base_class = base_class[0]

    newtree = base_class()
    newtree.id = tree.id
    newtree.rid = tree.rid
    newtree.xid = tree.xid
    newtree.sub = []

    for subtree in tree.sub:
        newtree.sub.append(to_base_placeables(subtree))

    return newtree
