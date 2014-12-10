#!/usr/bin/env python

from translate.convert import po2xliff
from translate.storage import po
from translate.storage import poxliff
from translate.storage import lisa

class TestPO2XLIFF:

    def po2xliff(self, posource, sourcelanguage='en', targetlanguage=None):
        """helper that converts po source to xliff source without requiring files"""
        postore = po.pofile(posource)
        convertor = po2xliff.po2xliff()
        outputxliff = convertor.convertstore(postore, None, sourcelanguage=sourcelanguage, targetlanguage=targetlanguage)
        return poxliff.PoXliffFile(outputxliff)

    def getnode(self, xliff):
        """Retrieves the trans-unit node from the dom"""
        assert len(xliff.units) == 1
        unit = xliff.units[0]
        return unit
 
    def test_minimal(self):
        minipo = '''msgid "red"\nmsgstr "rooi"\n'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        print str(xliff)
        assert len(xliff.units) == 1
        assert xliff.translate("red") == "rooi"
        assert xliff.translate("bla") is None
 
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
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        print str(xliff)
        assert xliff.translate("Applications") == "Toepassings"
        assert xliff.translate("bla") is None
        xmltext = str(xliff)
        assert xmltext.index('<xliff ') >= 0
        assert xmltext.index(' version="1.1"') >= 0
        assert xmltext.index('<file')
        assert xmltext.index('source-language')
        assert xmltext.index('datatype')

    def test_multiline(self):
        """Test multiline po entry"""
        minipo = r'''msgid "First part "
"and extra"
msgstr "Eerste deel "
"en ekstra"'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        print str(xliff)
        assert xliff.translate('First part and extra') == 'Eerste deel en ekstra'

    def test_escapednewlines(self):
        """Test the escaping of newlines"""
        minipo = r'''msgid "First line\nSecond line"
msgstr "Eerste lyn\nTweede lyn"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert xliff.translate("First line\nSecond line") == "Eerste lyn\nTweede lyn"
        assert xliff.translate("First line\\nSecond line") is None
        assert xmltext.find("line\\nSecond") == -1
        assert xmltext.find("lyn\\nTweede") == -1
        assert xmltext.find("line\nSecond") > 0
        assert xmltext.find("lyn\nTweede") > 0

    def test_escapedtabs(self):
        """Test the escaping of tabs"""
        minipo = r'''msgid "First column\tSecond column"
msgstr "Eerste kolom\tTweede kolom"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert xliff.translate("First column\tSecond column") == "Eerste kolom\tTweede kolom"
        assert xliff.translate("First column\\tSecond column") is None
        assert xmltext.find("column\\tSecond") == -1
        assert xmltext.find("kolom\\tTweede") == -1
        assert xmltext.find("column\tSecond") > 0
        assert xmltext.find("kolom\tTweede") > 0

    def test_escapedquotes(self):
        """Test the escaping of quotes (and slash)"""
        minipo = r'''msgid "Hello \"Everyone\""
msgstr "Good day \"All\""

msgid "Use \\\"."
msgstr "Gebruik \\\"."
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert xliff.translate('Hello "Everyone"') == 'Good day "All"'
        assert xliff.translate(r'Use \".') == r'Gebruik \".'
        assert xmltext.find(r'\&quot;') > 0 or xmltext.find(r'\"') > 0
        assert xmltext.find(r"\\") == -1

    def getcontexttuples(self, node, namespace):
        """Returns all the information in the context nodes as a list of tuples
        of (type, text)"""
        contexts = node.findall(".//{%s}context" % namespace)
        return [(context.get("context-type"), lisa.getText(context)) for context in contexts]

    def test_locationcomments(self):
        minipo = r'''#: file.c:123 asdf.c
msgid "one"
msgstr "kunye"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert xliff.translate("one") == "kunye"
        assert len(xliff.units) == 1
        node = xliff.units[0].xmlelement
        contextgroups = node.findall(".//%s" % xliff.namespaced("context-group"))
        assert len(contextgroups) == 2
        for group in contextgroups:
            assert group.get("name") == "po-reference"
            assert group.get("purpose") == "location"
        tuples = self.getcontexttuples(node, xliff.namespace)
        assert tuples == [("sourcefile", "file.c"), ("linenumber", "123"), ("sourcefile", "asdf.c")]

    def test_othercomments(self):
        minipo = r'''# Translate?
# How?
msgid "one"
msgstr "kunye"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert xliff.translate("one") == "kunye"
        assert len(xliff.units) == 1
        node = xliff.units[0].xmlelement
        contextgroups = node.findall(".//%s" % xliff.namespaced("context-group"))
        assert len(contextgroups) == 1
        for group in contextgroups:
            assert group.get("name") == "po-entry"
            assert group.get("purpose") == "information"
        tuples = self.getcontexttuples(node, xliff.namespace)
        assert tuples == [("x-po-trancomment", "Translate?\nHow?")]

        assert xliff.units[0].getnotes("translator") == "Translate?\nHow?"


    def test_automaticcomments(self):
        minipo = r'''#. Don't translate.
#. Please
msgid "one"
msgstr "kunye"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert xliff.translate("one") == "kunye"
        assert len(xliff.units) == 1
        node = xliff.units[0].xmlelement
        contextgroups = node.findall(".//%s" % xliff.namespaced("context-group"))
        assert len(contextgroups) == 1
        for group in contextgroups:
            assert group.get("name") == "po-entry"
            assert group.get("purpose") == "information"
        tuples = self.getcontexttuples(node, xliff.namespace)
        assert tuples == [("x-po-autocomment", "Don't translate.\nPlease")]

    def test_header(self):
        minipo = r'''# Pulana  Translation for bla
# Hallo Ma!
#, fuzzy
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert len(xliff.units) == 1
        unit = xliff.units[0]
        assert unit.source == unit.target == "Content-Type: text/plain; charset=UTF-8\n"
        assert unit.xmlelement.get("restype") == "x-gettext-domain-header"
        assert unit.xmlelement.get("approved") != "yes"
        assert unit.xmlelement.get("{%s}space" % lisa.XML_NS) == "preserve"
        assert unit.getnotes("po-translator") == "Pulana  Translation for bla\nHallo Ma!"

    def test_fuzzy(self):
        minipo = r'''#, fuzzy
msgid "two"
msgstr "pedi"

msgid "three"
msgstr "raro"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert len(xliff.units) == 2
        assert xliff.units[0].isfuzzy()
        assert not xliff.units[1].isfuzzy()

    def test_germanic_plurals(self):
        minipo = r'''msgid "cow"
msgid_plural "cows"
msgstr[0] "inkomo"
msgstr[1] "iinkomo"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert len(xliff.units) == 1
        assert xliff.translate("cow") == "inkomo"
        
    def test_funny_plurals(self):
        minipo = r'''msgid "cow"
msgid_plural "cows"
msgstr[0] "inkomo"
msgstr[1] "iinkomo"
msgstr[2] "iiinkomo"
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert len(xliff.units) == 1
        assert xliff.translate("cow") == "inkomo"

    def test_language_tags(self):
        minipo = r'''msgid "Een"
msgstr "Uno"
'''
        xliff = self.po2xliff(minipo, "af", "es")
        assert xliff.sourcelanguage == "af"
        assert xliff.targetlanguage == "es"
        
    def test_variables(self):
        minipo = r'''msgid "%s%s%s%s has made %s his or her buddy%s%s"
msgstr "%s%s%s%s het %s sy/haar vriend/vriendin gemaak%s%s"'''
        xliff = self.po2xliff(minipo)
        print xliff.units[0].source
        assert xliff.units[0].source == "%s%s%s%s has made %s his or her buddy%s%s"

    def test_approved(self):
        minipo = r'''#, fuzzy
msgid "two"
msgstr "pedi"

msgid "three"
msgstr "raro"

msgid "four"
msgstr ""
'''
        xliff = self.po2xliff(minipo)
        print "The generated xml:"
        xmltext = str(xliff)
        print xmltext
        assert len(xliff.units) == 3
        assert xliff.units[0].xmlelement.get("approved") != "yes"
        assert not xliff.units[0].isapproved()
        assert xliff.units[1].xmlelement.get("approved") == "yes"
        assert xliff.units[1].isapproved()
        assert xliff.units[2].xmlelement.get("approved") != "yes"
        assert not xliff.units[2].isapproved()

