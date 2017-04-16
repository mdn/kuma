#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2007 Zuza Software Foundation
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
#

from lxml import etree
from translate.storage.placeables import lisa, StringElem
from translate.storage.placeables.xliff import Bx, Ex, G, UnknownXML, X

def test_xml_to_strelem():
    source = etree.fromstring(u'<source>a<x id="foo[1]/bar[1]/baz[1]"/></source>')
    elem = lisa.xml_to_strelem(source)
    assert elem.sub == [ StringElem(u'a'), X(id=u'foo[1]/bar[1]/baz[1]') ]

    source = etree.fromstring(u'<source>a<x id="foo[1]/bar[1]/baz[1]"/>é</source>')
    elem = lisa.xml_to_strelem(source)
    assert elem.sub == [ StringElem(u'a'), X(id=u'foo[1]/bar[1]/baz[1]'), StringElem(u'é') ]

    source = etree.fromstring(u'<source>a<g id="foo[2]/bar[2]/baz[2]">b<x id="foo[1]/bar[1]/baz[1]"/>c</g>é</source>')
    elem = lisa.xml_to_strelem(source)
    assert elem.sub == [ StringElem(u'a'), G(id=u'foo[2]/bar[2]/baz[2]', sub=[StringElem(u'b'), X(id=u'foo[1]/bar[1]/baz[1]'), StringElem(u'c')]), StringElem(u'é') ]

def test_xml_space():
    source = etree.fromstring(u'<source xml:space="default"> a <x id="foo[1]/bar[1]/baz[1]"/> </source>')
    elem = lisa.xml_to_strelem(source)
    print elem.sub
    assert elem.sub == [ StringElem(u'a '), X(id=u'foo[1]/bar[1]/baz[1]'), StringElem(u' ')]

def test_chunk_list():
    left  = StringElem([u'a', G(id='foo[2]/bar[2]/baz[2]', sub=[u'b', X(id='foo[1]/bar[1]/baz[1]'), u'c']), u'é'])
    right = StringElem([u'a', G(id='foo[2]/bar[2]/baz[2]', sub=[u'b', X(id='foo[1]/bar[1]/baz[1]'), u'c']), u'é'])
    assert left == right

def test_set_strelem_to_xml():
    source = etree.Element(u'source')
    lisa.strelem_to_xml(source, StringElem(u'a'))
    assert etree.tostring(source, encoding = 'UTF-8') == '<source>a</source>'

    source = etree.Element(u'source')
    lisa.strelem_to_xml(source, StringElem([u'a', u'é']))
    assert etree.tostring(source, encoding = 'UTF-8') == '<source>aé</source>'

    source = etree.Element(u'source')
    lisa.strelem_to_xml(source, StringElem(X(id='foo[1]/bar[1]/baz[1]')))
    assert etree.tostring(source, encoding = 'UTF-8') == '<source><x id="foo[1]/bar[1]/baz[1]"/></source>'

    source = etree.Element(u'source')
    lisa.strelem_to_xml(source, StringElem([u'a', X(id='foo[1]/bar[1]/baz[1]')]))
    assert etree.tostring(source, encoding = 'UTF-8') == '<source>a<x id="foo[1]/bar[1]/baz[1]"/></source>'

    source = etree.Element(u'source')
    lisa.strelem_to_xml(source, StringElem([u'a', X(id='foo[1]/bar[1]/baz[1]'), u'é']))
    assert etree.tostring(source, encoding = 'UTF-8') == '<source>a<x id="foo[1]/bar[1]/baz[1]"/>é</source>'

    source = etree.Element(u'source')
    lisa.strelem_to_xml(source, StringElem([u'a', G(id='foo[2]/bar[2]/baz[2]', sub=[u'b', X(id='foo[1]/bar[1]/baz[1]'), u'c']), u'é']))
    assert etree.tostring(source, encoding = 'UTF-8') == '<source>a<g id="foo[2]/bar[2]/baz[2]">b<x id="foo[1]/bar[1]/baz[1]"/>c</g>é</source>'

def test_unknown_xml_placeable():
    # The XML below is (modified) from the official XLIFF example file Sample_AlmostEverything_1.2_strict.xlf
    source = etree.fromstring(u"""<source xml:lang="en-us">Text <g id="_1_ski_040">g</g>TEXT<bpt id="_1_ski_139">bpt<sub>sub</sub>
               </bpt>TEXT<ept id="_1_ski_238">ept</ept>TEXT<ph id="_1_ski_337"/>TEXT<it id="_1_ski_436" pos="open">it</it>TEXT<mrk mtype="x-test">mrk</mrk>
               <x id="_1_ski_535"/>TEXT<bx id="_1_ski_634"/>TEXT<ex id="_1_ski_733"/>TEXT.</source>""")
    elem = lisa.xml_to_strelem(source)

    from copy import copy
    custom = StringElem([
        StringElem(u'Text '),
        G(u'g', id='_1_ski_040'),
        StringElem(u'TEXT'),
        UnknownXML(
            [
                StringElem(u'bpt'),
                UnknownXML(u'sub', xml_node=copy(source[1][0])),
                StringElem(u'\n               ')
            ],
            id='_1_ski_139',
            xml_node=copy(source[3])
        ),
        StringElem(u'TEXT'),
        UnknownXML(u'ept', id=u'_1_ski_238', xml_node=copy(source[2])),
        StringElem(u'TEXT'),
        UnknownXML(id='_1_ski_337', xml_node=copy(source[3])), # ph-tag
        StringElem(u'TEXT'),
        UnknownXML(u'it', id='_1_ski_436', xml_node=copy(source[4])),
        StringElem(u'TEXT'),
        UnknownXML(u'mrk', xml_node=copy(source[5])),
        StringElem(u'\n               '),
        X(id='_1_ski_535'),
        StringElem(u'TEXT'),
        Bx(id='_1_ski_634'),
        StringElem(u'TEXT'),
        Ex(id='_1_ski_733'),
        StringElem(u'TEXT.')
    ])
    assert elem == custom

    xml = copy(source)
    for i in range(len(xml)):
        del xml[0]
    xml.text = None
    xml.tail = None
    lisa.strelem_to_xml(xml, elem)
    assert etree.tostring(xml) == etree.tostring(source)

if __name__ == '__main__':
    test_chunk_list()
    test_xml_to_strelem()
    test_set_strelem_to_xml()
    test_unknown_xml_placeable()
