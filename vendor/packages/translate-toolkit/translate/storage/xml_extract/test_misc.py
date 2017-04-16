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

from translate.storage.xml_extract import misc

# reduce_tree

test_tree_1 = (u'a',
               [(u'b', []),
                (u'c', [(u'd', []), (u'e', [])]),
                (u'f', [(u'g', [(u'h', [])])])])

test_tree_2 = (1,
               [(2, []),
                (3, [(4, []), (5, [])]),
                (6, [(7, [(8, [])])])])


def get_children(node):
    return node[1]

def test_reduce_tree():
    def concatenate(parent_node, node, string):
        return string + node[0]

    assert u'abcdefgh' == misc.reduce_tree(concatenate, test_tree_1, test_tree_1, get_children, u'')

    def get_even_and_total(parent_node, node, even_lst, total):
        num = node[0]
        if num % 2 == 0:
            even_lst.append(num)
        return even_lst, total + num

    assert ([2, 4, 6, 8], 36) == misc.reduce_tree(get_even_and_total, test_tree_2, test_tree_2, get_children, [], 0)

# compose_mappings

left_mapping     = {1:    u'a', 2:    u'b', 3: u'c', 4: u'd',  5: u'e'}
right_mapping    = {u'a': -1,   u'b': -2,            u'd': -4, u'e': -5, u'f': -6}

composed_mapping = {1: -1,      2: -2,               4: -4,    5: -5}

def test_compose_mappings():
    assert composed_mapping == misc.compose_mappings(left_mapping, right_mapping)

# parse_tag

def test_parse_tag():
    assert (u'some-urn', u'some-tag') == \
        misc.parse_tag(u'{some-urn}some-tag')

    assert (u'urn:oasis:names:tc:opendocument:xmlns:office:1.0', u'document-content') == \
        misc.parse_tag(u'{urn:oasis:names:tc:opendocument:xmlns:office:1.0}document-content')

