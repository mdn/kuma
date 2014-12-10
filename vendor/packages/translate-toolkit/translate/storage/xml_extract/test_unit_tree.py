#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2006 Zuza Software Foundation
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

from translate.storage.xml_extract import unit_tree
from translate.storage import factory

# _split_xpath_component

def test__split_xpath_component():
    assert ('some-tag', 0) == unit_tree._split_xpath_component('some-tag[0]')

# _split_xpath

def test__split_xpath():
    assert [(u'p', 4), (u'text', 3), (u'body', 2), (u'document-content', 1)] == \
        unit_tree._split_xpath(u'document-content[1]/body[2]/text[3]/p[4]')
    
# _add_unit_to_tree

def make_tree_1(unit):
    root = unit_tree.XPathTree()
    node = root
    
    node.children[u'document-content', 1] = unit_tree.XPathTree()
    node = node.children[u'document-content', 1]
    
    node.children[u'body', 1] = unit_tree.XPathTree()
    node = node.children[u'body', 1]

    node.children[u'text', 1] = unit_tree.XPathTree()
    node = node.children[u'text', 1]
    
    node.children[u'p', 1] = unit_tree.XPathTree()
    node = node.children[u'p', 1]

    node.unit = unit

    return root

def make_tree_2(unit_1, unit_2):
    root = make_tree_1(unit_1)
    node = root.children[u'document-content', 1]
    
    node.children[u'body', 2] = unit_tree.XPathTree()
    node = node.children[u'body', 2]

    node.children[u'text', 3] = unit_tree.XPathTree()
    node = node.children[u'text', 3]
    
    node.children[u'p', 4] = unit_tree.XPathTree()
    node = node.children[u'p', 4]

    node.unit = unit_2

    return root

def test__add_unit_to_tree():
    xliff_file = factory.classes[u'xlf']()

    # Add the first unit
    
    unit_1 = xliff_file.UnitClass(u'Hello')
    xpath_1 = u'document-content[1]/body[1]/text[1]/p[1]'

    constructed_tree_1 = unit_tree.XPathTree()
    unit_tree._add_unit_to_tree(constructed_tree_1,
                                unit_tree._split_xpath(xpath_1), 
                                unit_1)
    test_tree_1 = make_tree_1(unit_1)
    assert test_tree_1 == constructed_tree_1

    # Add another unit

    unit_2 = xliff_file.UnitClass(u'World')
    xpath_2 = u'document-content[1]/body[2]/text[3]/p[4]'
    
    constructed_tree_2 = make_tree_1(unit_1)
    unit_tree._add_unit_to_tree(constructed_tree_2, 
                                unit_tree._split_xpath(xpath_2),
                                unit_2)
    test_tree_2 = make_tree_2(unit_1, unit_2)
    assert test_tree_2 == constructed_tree_2
