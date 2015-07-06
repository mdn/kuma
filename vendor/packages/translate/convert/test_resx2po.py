#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Zuza Software Foundation
# Copyright 2015 Sarah Hale
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

""" Tests converting .Net Resource (.resx) to Gettext PO localisation files """

from translate.convert import test_convert, resx2po
from translate.misc import wStringIO
from translate.storage import po, resx
from translate.storage.poheader import poheader
from translate.storage.test_base import headerless_len


class TestRESX2PO:
    target_filetype = po.pofile
    XMLskeleton = '''<?xml version="1.0" encoding="utf-8"?>
    <root>
      <xsd:schema id="root" xmlns="" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata">
        <xsd:import namespace="http://www.w3.org/XML/1998/namespace" />
        <xsd:element name="root" msdata:IsDataSet="true">
          <xsd:complexType>
            <xsd:choice maxOccurs="unbounded">
              <xsd:element name="metadata">
                <xsd:complexType>
                  <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="0" />
                  </xsd:sequence>
                  <xsd:attribute name="name" use="required" type="xsd:string" />
                  <xsd:attribute name="type" type="xsd:string" />
                  <xsd:attribute name="mimetype" type="xsd:string" />
                  <xsd:attribute ref="xml:space" />
                </xsd:complexType>
              </xsd:element>
              <xsd:element name="assembly">
                <xsd:complexType>
                  <xsd:attribute name="alias" type="xsd:string" />
                  <xsd:attribute name="name" type="xsd:string" />
                </xsd:complexType>
              </xsd:element>
              <xsd:element name="data">
                <xsd:complexType>
                  <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
                    <xsd:element name="comment" type="xsd:string" minOccurs="0" msdata:Ordinal="2" />
                  </xsd:sequence>
                  <xsd:attribute name="name" type="xsd:string" use="required" msdata:Ordinal="1" />
                  <xsd:attribute name="type" type="xsd:string" msdata:Ordinal="3" />
                  <xsd:attribute name="mimetype" type="xsd:string" msdata:Ordinal="4" />
                  <xsd:attribute ref="xml:space" />
                </xsd:complexType>
              </xsd:element>
              <xsd:element name="resheader">
                <xsd:complexType>
                  <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
                  </xsd:sequence>
                  <xsd:attribute name="name" type="xsd:string" use="required" />
                </xsd:complexType>
              </xsd:element>
            </xsd:choice>
          </xsd:complexType>
        </xsd:element>
      </xsd:schema>
      <resheader name="resmimetype">
        <value>text/microsoft-resx</value>
      </resheader>
      <resheader name="version">
        <value>2.0</value>
      </resheader>
      %s
    </root>
    '''

    def resx2po(self, resxsource, template=None, filter=None):
        """ Helper that converts resx source to po source without requiring files """
        inputfile = wStringIO.StringIO(resxsource)
        inputresx = resx.RESXFile(inputfile)
        convertor = resx2po.resx2po()
        outputpo = convertor.convert_store(inputresx)
        return outputpo

    def test_simple(self):
        """ Test the most basic resx conversion """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        </data>'''
        poexpected = '''#: key
msgid "A simple string"
msgstr ""
'''
        po_result = self.resx2po(resx_source)

        assert str(po_result.units[1]) == poexpected
        assert headerless_len(po_result.units) == 1

    def test_multiple_units(self):
        """ Test that we can handle resx with multiple units """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        </data>
        <data name="key_two" xml:space="preserve">
        <value>A second simple string with a @@placeholder@@</value>
        </data>'''

        po_result = self.resx2po(resx_source)
        assert po_result.units[0].isheader()
        assert len(po_result.units) == 3

    def test_automaticcomments(self):
        """ Tests developer comments """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        <comment>This is a comment</comment>
        </data>
        <data name="key_two" xml:space="preserve">
        <value>A second simple string with a @@placeholder@@</value>
        </data>'''
        po_result = self.resx2po(resx_source)

        assert len(po_result.units) == 3
        assert po_result.units[1].getnotes("developer") == u"This is a comment"
        assert po_result.units[2].getnotes("developer") == u""

    def test_translatorcomments(self):
        """ Tests translator comments """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        <comment>This is a developer comment
[Translator Comment: This is a translator comment]</comment>
        </data>
        <data name="key_two" xml:space="preserve">
        <value>A second simple string with a @@placeholder@@</value>
        </data>'''
        po_result = self.resx2po(resx_source)

        assert len(po_result.units) == 3
        assert po_result.units[1].getnotes("developer") == u"This is a developer comment"
        assert po_result.units[1].getnotes("translator") == u"This is a translator comment"
        assert po_result.units[2].getnotes("developer") == u""
        assert po_result.units[2].getnotes("translator") == u""

    def test_locations(self):
        """ Tests location comments (#:) """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        <comment>This is a developer comment</comment>
        </data>
        <data name="key_two" xml:space="preserve">
        <value>A second simple string with a @@placeholder@@</value>
        </data>'''

        po_result = self.resx2po(resx_source)

        assert len(po_result.units) == 3
        assert po_result.units[1].getlocations()[0].startswith("key")
        assert po_result.units[2].getlocations()[0].startswith("key_two")

class TestRESX2POCommand(test_convert.TestConvertCommand, TestRESX2PO):
    """ Tests running actual resx2po commands on files """
    convertmodule = resx2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """ Tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot")
        options = self.help_check(options, "--duplicates")
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--filter", last=True)

    def single_element(self, pofile):
        """ Checks that the pofile contains a single non-header element, and returns it """
        if isinstance(pofile, poheader):
            assert len(pofile.units) == 2
            assert pofile.units[0].isheader()
            return pofile.units[1]
        else:
            assert len(pofile.units) == 1
            return pofile.units[0]

    def test_simple_pot(self):
        """ Tests the simplest possible conversion to a pot file """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        </data>'''

        self.create_testfile("simple.resx", resx_source)
        self.run_command("simple.resx", "simple.pot", pot=True)
        po_result = po.pofile(self.open_testfile("simple.pot"))
        po_element = self.single_element(po_result)

        assert po_element.source == u"A simple string"
        assert po_element.target == u""

    def test_simple_po(self):
        """ Tests the simplest possible conversion to a po file """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        </data>'''
        self.create_testfile("simple.resx", resx_source)
        self.run_command("simple.resx", "simple.po")
        po_result = po.pofile(self.open_testfile("simple.po"))
        po_element = self.single_element(po_result)
        assert po_element.source == "A simple string"
        assert po_element.target == ""

    def test_remove_duplicates(self):
        """ Test that removing of duplicates works correctly """
        resx_source = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>A simple string</value>
        </data>
        <data name="key" xml:space="preserve">
        <value>A simple string</value>
        </data>'''
        self.create_testfile("simple.resx", resx_source)
        self.run_command("simple.resx", "simple.po", error="traceback", duplicates="merge")
        po_result = self.target_filetype(self.open_testfile("simple.po"))

        assert len(po_result.units) == 2
        assert po_result.units[1].source == u"A simple string"
