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

"""Contains XLIFF-specific placeables."""

from translate.storage.placeables import base
from translate.storage.placeables.strelem import StringElem

__all__ = ['Bpt', 'Ept', 'X', 'Bx', 'Ex', 'G', 'It', 'Sub', 'Ph', 'UnknownXML', 'parsers', 'to_xliff_placeables']


class Bpt(base.Bpt):
    pass


class Ept(base.Ept):
    pass


class Ph(base.Ph):
    pass


class It(base.It):
    pass


class G(base.G):
    pass


class Bx(base.Bx):
    pass


class Ex(base.Ex):
    pass


class X(base.X):
    pass


class Sub(base.Sub):
    pass


class UnknownXML(StringElem):
    """Placeable for unrecognized or umimplemented XML nodes. It's main
        purpose is to preserve all associated XML data."""
    iseditable = True

    # INITIALIZERS #
    def __init__(self, sub=None, id=None, rid=None, xid=None, xml_node=None, **kwargs):
        super(UnknownXML, self).__init__(sub=sub, id=id, rid=rid, xid=xid, **kwargs)
        if xml_node is None:
            raise ValueError('xml_node must be a lxml node')
        self.xml_node = xml_node

        if sub:
            self.has_content = True


    # SPECIAL METHODS #
    def __repr__(self):
        """String representation of the sub-tree with the current node as the
            root.

            Copied from L{StringElem.__repr__}, but includes C{self.xml_node.tag}."""
        tag = self.xml_node.tag
        if tag.startswith('{'):
            tag = tag[tag.index('}')+1:]

        elemstr = ', '.join([repr(elem) for elem in self.sub])

        return '<%(class)s{%(tag)s}(%(id)s%(rid)s%(xid)s[%(subs)s])>' % {
            'class': self.__class__.__name__,
            'tag': tag,
            'id':  self.id  is not None and 'id="%s" '  % (self.id) or '',
            'rid': self.rid is not None and 'rid="%s" ' % (self.rid) or '',
            'xid': self.xid is not None and 'xid="%s" ' % (self.xid) or '',
            'subs': elemstr
        }


    # METHODS #
    def copy(self):
        """Returns a copy of the sub-tree.
            This should be overridden in sub-classes with more data.

            NOTE: C{self.renderer} is B{not} copied."""
        from copy import copy
        cp = self.__class__(id=self.id, rid=self.rid, xid=self.xid, xml_node=copy(self.xml_node))
        for sub in self.sub:
            if isinstance(sub, StringElem):
                cp.sub.append(sub.copy())
            else:
                cp.sub.append(sub.__class__(sub))
        return cp


def to_xliff_placeables(tree):
    if not isinstance(tree, StringElem):
        return tree

    newtree = None

    classmap = {
        base.Bpt: Bpt,
        base.Ept: Ept,
        base.Ph:  Ph,
        base.It:  It,
        base.G:   G,
        base.Bx:  Bx,
        base.Ex:  Ex,
        base.X:   X,
        base.Sub: Sub
    }
    for baseclass, xliffclass in classmap.items():
        if isinstance(tree, baseclass):
            newtree = xliffclass()

    if newtree is None:
        newtree = tree.__class__()

    newtree.id = tree.id
    newtree.rid = tree.rid
    newtree.xid = tree.xid
    newtree.sub = []

    for subtree in tree.sub:
        newtree.sub.append(to_xliff_placeables(subtree))

    return newtree


parsers = []
