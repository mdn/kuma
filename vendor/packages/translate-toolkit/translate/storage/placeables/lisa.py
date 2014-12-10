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

from lxml import etree

from translate.misc.xml_helpers import *
from translate.storage.placeables import base, xliff, StringElem
from translate.storage.xml_extract import misc

__all__ = ['xml_to_strelem', 'strelem_to_xml']
# Use the above functions as entry points into this module. The rest are used by these functions.


def make_empty_replacement_placeable(klass, node, xml_space="preserve"):
    try:
        return klass(
            id=node.attrib[u'id'],
            rid=node.attrib.get('rid', None),
            xid=node.attrib.get('xid', None),
            xml_attrib=node.attrib
        )
    except KeyError:
        pass
    return klass()

def make_g_placeable(klass, node, xml_space="default"):
    return klass(
        id=node.attrib[u'id'],
        sub=xml_to_strelem(node, xml_space).sub,
        xml_attrib=node.attrib
    )

def not_yet_implemented(klass, node, xml_space="preserve"):
    raise NotImplementedError

def make_unknown(klass, node, xml_space="preserve"):
    assert klass is xliff.UnknownXML

    sub = xml_to_strelem(node, xml_space).sub
    id =  node.get('id',  None)
    rid = node.get('rid', None)
    xid = node.get('xid', None)

    return klass(sub=sub, id=id, rid=rid, xid=xid, xml_node=node)

_class_dictionary = {
    #u'bpt': (xliff.Bpt, not_yet_implemented),
    u'bx' : (xliff.Bx,  make_empty_replacement_placeable),
    #u'ept': (xliff.Ept, not_yet_implemented),
    u'ex' : (xliff.Ex,  make_empty_replacement_placeable),
    u'g'  : (xliff.G,   make_g_placeable),
    #u'it' : (xliff.It,  not_yet_implemented),
    #u'ph' : (xliff.Ph,  not_yet_implemented),
    #u'sub': (xliff.Sub, not_yet_implemented),
    u'x'  : (xliff.X,   make_empty_replacement_placeable)
}

def make_placeable(node, xml_space):
    _namespace, tag = misc.parse_tag(node.tag)
    if tag in _class_dictionary:
        klass, maker = _class_dictionary[tag]
    else:
        klass, maker = xliff.UnknownXML, make_unknown
    return maker(klass, node, xml_space)

def as_unicode(string):
    if isinstance(string, unicode):
        return string
    elif isinstance(string, StringElem):
        return unicode(string)
    else:
        return unicode(string.decode('utf-8'))

def xml_to_strelem(dom_node, xml_space="preserve"):
    if dom_node is None:
        return StringElem()
    if isinstance(dom_node, basestring):
        dom_node = etree.fromstring(dom_node)
    normalize_xml_space(dom_node, xml_space, remove_start=True)
    result = StringElem()
    if dom_node.text:
        result.sub.append(StringElem(unicode(dom_node.text)))
    for child_dom_node in dom_node:
        result.sub.append(make_placeable(child_dom_node, xml_space))
        if child_dom_node.tail:
            result.sub.append(StringElem(unicode(child_dom_node.tail)))
    result.prune()
    return result

# ==========================================================

def placeable_as_dom_node(placeable, tagname):
    dom_node = etree.Element(tagname)
    if placeable.id is not None:
        dom_node.attrib['id'] = placeable.id
    if placeable.xid is not None:
        dom_node.attrib['xid'] = placeable.xid
    if placeable.rid is not None:
        dom_node.attrib['rid'] = placeable.rid

    if hasattr(placeable, 'xml_attrib'):
        for attrib, value in placeable.xml_attrib.items():
            dom_node.set(attrib, value)

    return dom_node

def unknown_placeable_as_dom_node(placeable):
    assert type(placeable) is xliff.UnknownXML

    from copy import copy
    node = copy(placeable.xml_node)
    for i in range(len(node)):
        del node[0]
    node.tail = None
    node.text = None

    return node

_placeable_dictionary = {
    xliff.Bpt: lambda placeable: placeable_as_dom_node(placeable, 'bpt'),
    xliff.Bx : lambda placeable: placeable_as_dom_node(placeable, 'bx'),
    xliff.Ept: lambda placeable: placeable_as_dom_node(placeable, 'ept'),
    xliff.Ex : lambda placeable: placeable_as_dom_node(placeable, 'ex'),
    xliff.G  : lambda placeable: placeable_as_dom_node(placeable, 'g'),
    xliff.It : lambda placeable: placeable_as_dom_node(placeable, 'it'),
    xliff.Ph : lambda placeable: placeable_as_dom_node(placeable, 'ph'),
    xliff.Sub: lambda placeable: placeable_as_dom_node(placeable, 'sub'),
    xliff.X  : lambda placeable: placeable_as_dom_node(placeable, 'x'),
    xliff.UnknownXML: unknown_placeable_as_dom_node,
    base.Bpt:  lambda placeable: placeable_as_dom_node(placeable, 'bpt'),
    base.Bx :  lambda placeable: placeable_as_dom_node(placeable, 'bx'),
    base.Ept:  lambda placeable: placeable_as_dom_node(placeable, 'ept'),
    base.Ex :  lambda placeable: placeable_as_dom_node(placeable, 'ex'),
    base.G  :  lambda placeable: placeable_as_dom_node(placeable, 'g'),
    base.It :  lambda placeable: placeable_as_dom_node(placeable, 'it'),
    base.Ph :  lambda placeable: placeable_as_dom_node(placeable, 'ph'),
    base.Sub:  lambda placeable: placeable_as_dom_node(placeable, 'sub'),
    base.X  :  lambda placeable: placeable_as_dom_node(placeable, 'x')
}

def xml_append_string(node, string):
    if not len(node):
        if not node.text:
            node.text = unicode(string)
        else:
            node.text += unicode(string)
    else:
        lastchild = node.getchildren()[-1]
        if lastchild.tail is None:
            lastchild.tail = ''
        lastchild.tail += unicode(string)
    return node

def strelem_to_xml(parent_node, elem):
    if isinstance(elem, (str, unicode)):
        return xml_append_string(parent_node, elem)
    if not isinstance(elem, StringElem):
        return parent_node

    if type(elem) is StringElem and elem.isleaf():
        return xml_append_string(parent_node, elem)

    if elem.__class__ in _placeable_dictionary:
        node = _placeable_dictionary[elem.__class__](elem)
        parent_node.append(node)
    else:
        node = parent_node

    for sub in elem.sub:
        strelem_to_xml(node, sub)

    return parent_node


def parse_xliff(pstr):
    try:
        return xml_to_strelem(etree.fromstring('<source>%s</source>' % (pstr)))
    except Exception, exc:
        raise
        return None
xliff.parsers = [parse_xliff]
