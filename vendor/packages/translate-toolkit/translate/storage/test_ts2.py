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

from translate.misc.multistring import multistring
from translate.storage import ts2 as ts
from translate.storage import test_base
from translate.storage.placeables import parse
from translate.storage.placeables import xliff
from translate.storage.placeables.lisa import xml_to_strelem


xliffparsers = []
for attrname in dir(xliff):
    attr = getattr(xliff, attrname)
    if  type(attr) is type and attrname not in ('XLIFFPlaceable') and hasattr(attr, 'parse') and attr.parse is not None:
        xliffparsers.append(attr.parse)

def rich_parse(s):
    return parse(s, xliffparsers)


class TestTSUnit(test_base.TestTranslationUnit):
    UnitClass = ts.tsunit

class TestTSfile(test_base.TestTranslationStore):
    StoreClass = ts.tsfile
    def test_basic(self):
        tsfile = ts.tsfile()
        assert tsfile.units == []
        tsfile.addsourceunit("Bla")
        assert len(tsfile.units) == 1
        newfile = ts.tsfile.parsestring(str(tsfile))
        print str(tsfile)
        assert len(newfile.units) == 1
        assert newfile.units[0].source == "Bla"
        assert newfile.findunit("Bla").source == "Bla"
        assert newfile.findunit("dit") is None
    
    def test_source(self):
        tsfile = ts.tsfile()
        tsunit = tsfile.addsourceunit("Concept")
        tsunit.source = "Term"
        newfile = ts.tsfile.parsestring(str(tsfile))
        print str(tsfile)
        assert newfile.findunit("Concept") is None
        assert newfile.findunit("Term") is not None
    
    def test_target(self):
        tsfile = ts.tsfile()
        tsunit = tsfile.addsourceunit("Concept")
        tsunit.target = "Konsep"
        newfile = ts.tsfile.parsestring(str(tsfile))
        print str(tsfile)
        assert newfile.findunit("Concept").target == "Konsep"
		
