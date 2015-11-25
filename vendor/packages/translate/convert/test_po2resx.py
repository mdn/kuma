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

""" Tests converting Gettext PO localisation files to .Net Resource (.resx) files """

from translate.convert import po2resx, test_convert
from translate.storage import po
from translate.misc import wStringIO


class TestPO2RESX:
    XMLskeleton = '''<?xml version='1.0' encoding='utf-8'?>
<root>
  <xsd:schema xmlns="" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata" id="root">
    <xsd:import namespace="http://www.w3.org/XML/1998/namespace"/>
    <xsd:element name="root" msdata:IsDataSet="true">
      <xsd:complexType>
        <xsd:choice maxOccurs="unbounded">
          <xsd:element name="metadata">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0"/>
              </xsd:sequence>
              <xsd:attribute name="name" use="required" type="xsd:string"/>
              <xsd:attribute name="type" type="xsd:string"/>
              <xsd:attribute name="mimetype" type="xsd:string"/>
              <xsd:attribute ref="xml:space"/>
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="assembly">
            <xsd:complexType>
              <xsd:attribute name="alias" type="xsd:string"/>
              <xsd:attribute name="name" type="xsd:string"/>
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="data">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1"/>
                <xsd:element name="comment" type="xsd:string" minOccurs="0" msdata:Ordinal="2"/>
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required" msdata:Ordinal="1"/>
              <xsd:attribute name="type" type="xsd:string" msdata:Ordinal="3"/>
              <xsd:attribute name="mimetype" type="xsd:string" msdata:Ordinal="4"/>
              <xsd:attribute ref="xml:space"/>
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="resheader">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1"/>
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required"/>
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

    def po2resx(self, resxsource, po_source):
        """ Helper that merges po translations to .resx source without requiring files """
        po_store = po.pofile(po_source)
        template_file = wStringIO.StringIO(resxsource)
        convertor = po2resx.po2resx(template_file, po_store)
        output_resx = convertor.convertstore()
        return output_resx

    def test_simpleunit(self):
        """ Checks that a simple po entry definition converts properly to a resx entry """
        po_source = r'''#: key
msgid "Source Text"
msgstr "Some translated text"'''
        resx_template = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="key" xml:space="preserve">
        <value>Some translated text</value>
    </data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_basic(self):
        po_source = r"""# Afrikaans translation of program ABC
#
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2014-12-22 23:20+0000\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

#: ResourceKey
msgid "Applications"
msgstr "Toepassings"
"""
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Toepassings</value>
    </data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_multiline(self):
        """ Test multiline po entry """
        po_source = r'''#: ResourceKey
msgid "First part "
"and extra"
msgstr "Eerste deel "
"en ekstra"'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Eerste deel en ekstra</value>
    </data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_escapednewlines(self):
        """ Test the escaping of newlines """
        po_source = r'''#: ResourceKey
msgid "First line\nSecond line"
msgstr "Eerste lyn\nTweede lyn"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Eerste lyn
Tweede lyn</value>
    </data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_escapedtabs(self):
        """ Test the escaping of tabs """
        po_source = r'''#: ResourceKey
msgid "First column\tSecond column"
msgstr "Eerste kolom\tTweede kolom"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Eerste kolom\tTweede kolom</value>
    </data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_escapedquotes(self):
        """ Test the escaping of quotes (and slash) """
        po_source = r'''#: ResourceKey
msgid "Hello \"Everyone\""
msgstr "Good day \"All\""

msgid "Use \\\"."
msgstr "Gebruik \\\"."
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Good day "All"</value>
    </data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_exclusions(self):
        """ Test that empty and fuzzy messages are excluded """
        po_source = r'''#: ResourceKey
#, fuzzy
msgid "One"
msgstr "Een"

#: ResourceKey2
msgid "Two"
msgstr ""

#: ResourceKey3
msgid ""
msgstr "Drie"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value/>
    </data>
<data name="ResourceKey2" xml:space="preserve">
    <value/>
</data>
<data name="ResourceKey3" xml:space="preserve">
    <value/>
</data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value/>
    </data>
<data name="ResourceKey2" xml:space="preserve">
    <value/>
</data>
<data name="ResourceKey3" xml:space="preserve">
    <value/>
</data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_automaticcomments(self):
        """ Tests that automatic comments are imported """
        po_source = r'''#. This is a comment
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is a comment</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_automaticcomments_existingcomment(self):
        """ Tests a differing automatic comment is added if there is an existing automatic comment """
        po_source = r'''#. This is a new comment
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment>This is an existing comment</comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is an existing comment
This is a new comment</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_automaticcomments_existingduplicatecomment(self):
        """ Tests there is no duplication of automatic comments if it already exists and hasn't changed """
        po_source = r'''#. This is an existing comment
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment>This is an existing comment</comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is an existing comment</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_automaticcomments_existingduplicatecommentwithwhitespace(self):
        """ Tests there is no duplication of automatic comments if it already exists, hasn't changed but has leading or
        trailing whitespaces """
        po_source = r'''#.  This is an existing comment with leading and trailing spaces
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment> This is an existing comment with leading and trailing spaces </comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is an existing comment with leading and trailing spaces</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_translatorcomments(self):
        """ Tests that translator comments are imported """
        po_source = r'''# This is a translator comment : 22.12.14
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>[Translator Comment: This is a translator comment : 22.12.14]</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_translatorcomments_existingcomment(self):
        """ Tests a differing translator comment is added if there is an existing translator comment """
        po_source = r'''# This is a new translator comment
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment>[Translator Comment: This is an existing comment]</comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>[Translator Comment: This is an existing comment]
[Translator Comment: This is a new translator comment]</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_translatorcomments_existingduplicatecomment(self):
        """ Tests there is no duplication of translator comments if it already exists and hasn't changed """
        po_source = r'''# This is an existing translator comment
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment>[Translator Comment: This is an existing translator comment]</comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>[Translator Comment: This is an existing translator comment]</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_combocomments(self):
        """ Tests that translator comments and automatic comments are imported """
        po_source = r'''#. This is a developer comment
# This is a translator comment : 22.12.14
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        </data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is a developer comment
[Translator Comment: This is a translator comment : 22.12.14]</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_combocomments_existingduplicatecomment(self):
        """ Tests there is no duplication of automatic comment if it already exists and hasn't changed, but still adds
        the translator comment """
        po_source = r'''#. This is an existing comment
# This is a translator comment : 22.12.14
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment>This is an existing comment</comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is an existing comment
[Translator Comment: This is a translator comment : 22.12.14]</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_combocomments_existingcomment(self):
        """ Tests a differing automatic comment is added if there is an existing automatic comment, but still adds
        the translator comment """
        po_source = r'''#. This is a new comment
# This is a translator comment : 22.12.14
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment>This is an existing comment</comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is an existing comment
This is a new comment
[Translator Comment: This is a translator comment : 22.12.14]</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output

    def test_existingcomments(self):
        """ Tests that no extra space is added when there are no changes to existing comments"""
        po_source = r'''#. This is an existing comment
# This is an existing translator comment : 22.12.14
#: ResourceKey
msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        resx_template = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value></value>
        <comment>This is an existing comment
[Translator Comment: This is an existing translator comment : 22.12.14]</comment></data>'''
        expected_output = self.XMLskeleton % '''<data name="ResourceKey" xml:space="preserve">
        <value>Bézier-kurwe</value>
    <comment>This is an existing comment
[Translator Comment: This is an existing translator comment : 22.12.14]</comment></data>'''
        resx_file = self.po2resx(resx_template, po_source)
        assert resx_file == expected_output


class TestPO2TSCommand(test_convert.TestConvertCommand, TestPO2RESX):
    """ Tests running actual po2ts commands on files """
    convertmodule = po2resx

    def test_help(self):
        """ Tests getting help """
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
