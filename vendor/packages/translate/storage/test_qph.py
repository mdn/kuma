#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2010 Zuza Software Foundation
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

"""Tests for Qt Linguist phase book storage class"""

from translate.storage import qph, test_base
from translate.storage.placeables import parse, xliff


xliffparsers = []
for attrname in dir(xliff):
    attr = getattr(xliff, attrname)
    if type(attr) is type and \
       attrname not in ('XLIFFPlaceable') and \
       hasattr(attr, 'parse') and \
       attr.parse is not None:
        xliffparsers.append(attr.parse)


def rich_parse(s):
    return parse(s, xliffparsers)


class TestQphUnit(test_base.TestTranslationUnit):
    UnitClass = qph.QphUnit


class TestQphFile(test_base.TestTranslationStore):
    StoreClass = qph.QphFile

    def test_basic(self):
        qphfile = self.StoreClass()
        assert qphfile.units == []
        qphfile.addsourceunit("Bla")
        assert len(qphfile.units) == 1
        newfile = qph.QphFile.parsestring(str(qphfile))
        print(str(qphfile))
        assert len(newfile.units) == 1
        assert newfile.units[0].source == "Bla"
        assert newfile.findunit("Bla").source == "Bla"
        assert newfile.findunit("dit") is None

    def test_source(self):
        qphfile = qph.QphFile()
        qphunit = qphfile.addsourceunit("Concept")
        qphunit.source = "Term"
        newfile = qph.QphFile.parsestring(str(qphfile))
        print(str(qphfile))
        assert newfile.findunit("Concept") is None
        assert newfile.findunit("Term") is not None

    def test_target(self):
        qphfile = qph.QphFile()
        qphunit = qphfile.addsourceunit("Concept")
        qphunit.target = "Konsep"
        newfile = qph.QphFile.parsestring(str(qphfile))
        print(str(qphfile))
        assert newfile.findunit("Concept").target == "Konsep"

    def test_language(self):
        """Check that we can get and set language and sourcelanguage
        in the header"""
        qphstr = '''<!DOCTYPE QPH>
<QPH language="fr" sourcelanguage="de">
</QPH>
'''
        qphfile = qph.QphFile.parsestring(qphstr)
        assert qphfile.gettargetlanguage() == 'fr'
        assert qphfile.getsourcelanguage() == 'de'
        qphfile.settargetlanguage('pt_BR')
        assert 'pt_BR' in str(qphfile)
        assert qphfile.gettargetlanguage() == 'pt-br'
        # We convert en_US to en
        qphstr = '''<!DOCTYPE QPH>
<QPH language="fr" sourcelanguage="en_US">
</QPH>
'''
        qphfile = qph.QphFile.parsestring(qphstr)
        assert qphfile.getsourcelanguage() == 'en'
