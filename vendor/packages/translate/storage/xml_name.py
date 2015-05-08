#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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
#


class XmlNamespace(object):

    def __init__(self, namespace):
        self._namespace = namespace

    def name(self, tag):
        return "{%s}%s" % (self._namespace, tag)


class XmlNamer(object):
    """Initialize me with a DOM node or a DOM document node (the
    toplevel node you get when parsing an XML file). Then use me
    to generate fully qualified XML names.

    >>> xml = '<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"></office>'
    >>> from lxml import etree
    >>> namer = XmlNamer(etree.fromstring(xml))
    >>> namer.name('office', 'blah')
    {urn:oasis:names:tc:opendocument:xmlns:office:1.0}blah
    >>> namer.name('office:blah')
    {urn:oasis:names:tc:opendocument:xmlns:office:1.0}blah

    I can also give you XmlNamespace objects if you give me the abbreviated
    namespace name. These are useful if you need to reference a namespace
    continuously.

    >>> office_ns = name.namespace('office')
    >>> office_ns.name('foo')
    {urn:oasis:names:tc:opendocument:xmlns:office:1.0}foo
    """

    def __init__(self, dom_node):
        # Allow the user to pass a dom node of the
        # XML document nodle
        if hasattr(dom_node, 'nsmap'):
            self.nsmap = dom_node.nsmap
        else:
            self.nsmap = dom_node.getroot().nsmap

    def name(self, namespace_shortcut, tag=None):
        # If the user doesn't pass an argument into 'tag'
        # then namespace_shortcut contains a tag of the form
        # 'short-namespace:tag'
        if tag is None:
            namespace_shortcut, tag = namespace_shortcut.split(':')
        return "{%s}%s" % (self.nsmap[namespace_shortcut], tag)

    def namespace(self, namespace_shortcut):
        return XmlNamespace(self.nsmap[namespace_shortcut])
