#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from translate.storage.placeables import base, general, parse, xliff, StringElem


class TestStringElem:
    ORIGSTR = u'Ģët <a href="http://www.example.com" alt="Ģët &brand;!">&brandLong;</a>'

    def __init__(self):
        self.elem = parse(self.ORIGSTR, general.parsers)

    def test_parse(self):
        assert unicode(self.elem) == self.ORIGSTR

    def test_tree(self):
        assert len(self.elem.sub) == 4
        assert unicode(self.elem.sub[0]) == u'Ģët '
        assert unicode(self.elem.sub[1]) == u'<a href="http://www.example.com" alt="Ģët &brand;!">'
        assert unicode(self.elem.sub[2]) == u'&brandLong;'
        assert unicode(self.elem.sub[3]) == u'</a>'

        assert len(self.elem.sub[0].sub) == 1 and self.elem.sub[0].sub[0] == u'Ģët '
        assert len(self.elem.sub[1].sub) == 1 and self.elem.sub[1].sub[0] == u'<a href="http://www.example.com" alt="Ģët &brand;!">'
        assert len(self.elem.sub[2].sub) == 1 and self.elem.sub[2].sub[0] == u'&brandLong;'
        assert len(self.elem.sub[3].sub) == 1 and self.elem.sub[3].sub[0] == u'</a>'

    def test_add(self):
        assert self.elem + ' ' == self.ORIGSTR + ' '
        # ... and __radd__() ... doesn't work
        #assert ' ' + self.elem == ' ' + self.ORIGSTR

    def test_contains(self):
        assert 'href' in self.elem
        assert u'hrȩf' not in self.elem

    def test_getitem(self):
        assert self.elem[0] == u'Ģ'
        assert self.elem[2] == 't'

    def test_getslice(self):
        assert self.elem[0:3] == u'Ģët'

    def test_iter(self):
        for chunk in self.elem:
            assert issubclass(chunk.__class__, StringElem)

    def test_len(self):
        assert len(self.elem) == len(self.ORIGSTR)

    def test_mul(self):
        assert self.elem * 2 == self.ORIGSTR * 2
        # ... and __rmul__()
        assert 2 * self.elem == 2 * self.ORIGSTR

    def test_elem_offset(self):
        assert self.elem.elem_offset(self.elem.sub[0]) == 0
        assert self.elem.elem_offset(self.elem.sub[1]) == 4

    def test_elem_at_offset(self):
        assert self.elem.elem_at_offset(0) is self.elem.sub[0]
        assert self.elem.elem_at_offset(self.elem.find('!')) is self.elem.sub[1]

    def test_find(self):
        assert self.elem.find('example') == 24
        assert self.elem.find(u'example') == 24
        searchelem = parse(u'&brand;', general.parsers)
        assert self.elem.find(searchelem) == 46

    def test_find_elems_with(self):
        assert self.elem.find_elems_with(u'Ģët') == [ self.elem.sub[0], self.elem.sub[1] ]
        assert len(self.elem.find_elems_with('a')) == 3

    def test_flatten(self):
        assert u''.join([unicode(i) for i in self.elem.flatten()]) == self.ORIGSTR

    def test_delete_range_case1(self):
        # Case 1: Entire string #
        elem = self.elem.copy()
        deleted, parent, offset = elem.delete_range(0, len(elem))
        assert deleted == self.elem
        assert parent is None and offset is None

    def test_delete_range_case2(self):
        # Case 2: An entire element #
        elem = self.elem.copy()
        offset = elem.elem_offset(elem.sub[2])
        deleted, parent, offset = elem.delete_range(offset, offset+len(elem.sub[2]))
        assert deleted == self.elem.sub[2]
        assert parent is elem
        assert offset == len(elem.sub[0]) + len(elem.sub[1])

    def test_delete_range_case3(self):
        # Case 3: Within a single element #
        elem = self.elem.copy()
        deleted, parent, offset = elem.delete_range(1, 2)
        assert deleted == StringElem(u'ë')
        assert parent is elem.sub[0]
        assert offset == 1

    def test_delete_range_case4(self):
        # Case 4: Across multiple elements #
        elem = self.elem.copy()
        # Delete the last two elements
        deleted, parent, offset = elem.delete_range(elem.elem_offset(elem.sub[2]), len(elem))
        assert deleted == self.elem
        assert parent is None
        assert offset is None
        assert len(elem.sub) == 2
        assert unicode(elem) == u'Ģët <a href="http://www.example.com" alt="Ģët &brand;!">'

        # A separate test case where the delete range include elements between
        # the start- and end elements.
        origelem = parse(u'foo %s bar', general.parsers)
        elem = origelem.copy()
        assert len(elem.sub) == 3
        deleted, parent, offset = elem.delete_range(3, 7)
        assert deleted == origelem
        assert parent is None
        assert offset is None
        assert unicode(elem) == 'foobar'

    def test_insert(self):
        # Test inserting at the beginning
        elem = self.elem.copy()
        elem.insert(0, u'xxx')
        assert unicode(elem.sub[0]) == u'xxx' + unicode(self.elem.sub[0])

        # Test inserting at the end
        elem = self.elem.copy()
        elem.insert(len(elem) + 1, u'xxx')
        assert elem.flatten()[-1] == StringElem(u'xxx')

        # Test inserting in the middle of an existing string
        elem = self.elem.copy()
        elem.insert(2, u'xxx')
        assert unicode(elem.sub[0]) == u'Ģëxxxt '

        # Test inserting between elements
        elem = self.elem.copy()
        elem.insert(56, u'xxx')
        assert unicode(elem)[56:59] == u'xxx'

    def test_isleaf(self):
        for child in self.elem.sub:
            assert child.isleaf()


class TestConverters:
    def __init__(self):
        self.elem = parse(TestStringElem.ORIGSTR, general.parsers)

    def test_to_base_placeables(self):
        basetree = base.to_base_placeables(self.elem)
        # The following asserts say that, even though tree and newtree represent the same string
        # (the unicode() results are the same), they are composed of different classes (and so
        # their repr()s are different
        assert unicode(self.elem) == unicode(basetree)
        assert repr(self.elem) != repr(basetree)

    def test_to_general_placeables(self):
        basetree = base.to_base_placeables(self.elem)
        gentree = general.to_general_placeables(basetree)
        assert gentree == self.elem

    # FIXME: Fix and enable the following test
    def DISABLED_test_to_xliff_placeables(self):
        basetree = base.to_base_placeables(self.elem)
        xliff_from_base = xliff.to_xliff_placeables(basetree)
        assert unicode(xliff_from_base) != unicode(self.elem)
        assert repr(xliff_from_base) != repr(self.elem)

        xliff_from_gen = xliff.to_xliff_placeables(self.elem)
        assert unicode(xliff_from_gen) != unicode(self.elem)
        assert repr(xliff_from_gen) != repr(self.elem)

        assert unicode(xliff_from_base) == unicode(xliff_from_gen)
        assert repr(xliff_from_base) == repr(xliff_from_gen)


if __name__ == '__main__':
    for test in [TestStringElem(), TestConverters()]:
        for method in dir(test):
            if method.startswith('test_') and callable(getattr(test, method)):
                getattr(test, method)()

    test.elem.print_tree()
