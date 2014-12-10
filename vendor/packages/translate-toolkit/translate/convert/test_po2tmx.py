#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import po2tmx
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import tmx
from translate.storage import lisa

class TestPO2TMX:

    def po2tmx(self, posource, sourcelanguage='en', targetlanguage='af'):
        """helper that converts po source to tmx source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        outputfile.tmxfile = tmx.tmxfile(inputfile=None, sourcelanguage=sourcelanguage)
        po2tmx.convertpo(inputfile, outputfile, templatefile=None, sourcelanguage=sourcelanguage, targetlanguage=targetlanguage)
        return outputfile.tmxfile

    def test_basic(self):
        minipo = r"""# Afrikaans translation of program ABC
#
msgid ""
msgstr ""
"Project-Id-Version: program 2.1-branch\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2006-01-09 07:15+0100\n"
"PO-Revision-Date: 2004-03-30 17:02+0200\n"
"Last-Translator: Zuza Software Foundation <xxx@translate.org.za>\n"
"Language-Team: Afrikaans <translate-discuss-xxx@lists.sourceforge.net>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

# Please remember to do something
#: ../dir/file.xml.in.h:1 ../dir/file2.xml.in.h:4
msgid "Applications"
msgstr "Toepassings"
"""
        tmx = self.po2tmx(minipo)
        print "The generated xml:"
        print str(tmx)
        assert tmx.translate("Applications") == "Toepassings"
        assert tmx.translate("bla") is None
        xmltext = str(tmx)
        assert xmltext.index('creationtool="Translate Toolkit - po2tmx"')
        assert xmltext.index('adminlang')
        assert xmltext.index('creationtoolversion')
        assert xmltext.index('datatype')
        assert xmltext.index('o-tmf')
        assert xmltext.index('segtype')
        assert xmltext.index('srclang')

    def test_sourcelanguage(self):
        minipo = 'msgid "String"\nmsgstr "String"\n'
        tmx = self.po2tmx(minipo, sourcelanguage="xh")
        print "The generated xml:"
        print str(tmx)
        header = tmx.document.find("header")
        assert header.get("srclang") == "xh"
        
    def test_targetlanguage(self):
        minipo = 'msgid "String"\nmsgstr "String"\n'
        tmx = self.po2tmx(minipo, targetlanguage="xh")
        print "The generated xml:"
        print str(tmx)
        tuv = tmx.document.findall(".//%s" % tmx.namespaced("tuv"))[1]
        #tag[0] will be the source, we want the target tuv
        assert tuv.get("{%s}lang" % lisa.XML_NS) == "xh"
        
    def test_multiline(self):
        """Test multiline po entry"""
        minipo = r'''msgid "First part "
"and extra"
msgstr "Eerste deel "
"en ekstra"'''
        tmx = self.po2tmx(minipo)
        print "The generated xml:"
        print str(tmx)
        assert tmx.translate('First part and extra') == 'Eerste deel en ekstra'

        
    def test_escapednewlines(self):
        """Test the escaping of newlines"""
        minipo = r'''msgid "First line\nSecond line"
msgstr "Eerste lyn\nTweede lyn"
'''
        tmx = self.po2tmx(minipo)
        print "The generated xml:"
        print str(tmx)
        assert tmx.translate("First line\nSecond line") == "Eerste lyn\nTweede lyn"

    def test_escapedtabs(self):
        """Test the escaping of tabs"""
        minipo = r'''msgid "First column\tSecond column"
msgstr "Eerste kolom\tTweede kolom"
'''
        tmx = self.po2tmx(minipo)
        print "The generated xml:"
        print str(tmx)
        assert tmx.translate("First column\tSecond column") == "Eerste kolom\tTweede kolom"

    def test_escapedquotes(self):
        """Test the escaping of quotes (and slash)"""
        minipo = r'''msgid "Hello \"Everyone\""
msgstr "Good day \"All\""

msgid "Use \\\"."
msgstr "Gebruik \\\"."
'''
        tmx = self.po2tmx(minipo)
        print "The generated xml:"
        print str(tmx)
        assert tmx.translate('Hello "Everyone"') == 'Good day "All"'
        assert tmx.translate(r'Use \".') == r'Gebruik \".'

    def test_exclusions(self):
        """Test that empty and fuzzy messages are excluded"""
        minipo = r'''#, fuzzy
msgid "One"
msgstr "Een"

msgid "Two"
msgstr ""

msgid ""
msgstr "Drie"
'''
        tmx = self.po2tmx(minipo)
        print "The generated xml:"
        print str(tmx)
        assert "<tu" not in str(tmx)
        assert len(tmx.units) == 0

    def test_nonascii(self):
        """Tests that non-ascii conversion works."""
        minipo = r'''msgid "Bézier curve"
msgstr "Bézier-kurwe"
'''
        tmx = self.po2tmx(minipo)
        print str(tmx)
        assert tmx.translate(u"Bézier curve") == u"Bézier-kurwe"


class TestPO2TMXCommand(test_convert.TestConvertCommand, TestPO2TMX):
    """Tests running actual po2tmx commands on files"""
    convertmodule = po2tmx

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-l LANG, --language=LANG")
        options = self.help_check(options, "--source-language=LANG", last=True)

