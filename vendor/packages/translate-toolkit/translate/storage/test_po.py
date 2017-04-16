#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import po
from translate.storage import pypo
from translate.storage import test_base
from translate.misc import wStringIO
from translate.misc.multistring import multistring
from py.test import raises

def test_roundtrip_quoting():
    specials = ['Fish & chips', 'five < six', 'six > five', 
                'Use &nbsp;', 'Use &amp;nbsp;' 
                'A "solution"', "skop 'n bal", '"""', "'''", 
                '\n', '\t', '\r', 
                '\\n', '\\t', '\\r', '\\"', '\r\n', '\\r\\n', '\\']
    for special in specials:
        quoted_special = pypo.quoteforpo(special)
        unquoted_special = pypo.unquotefrompo(quoted_special)
        print "special: %r\nquoted: %r\nunquoted: %r\n" % (special, quoted_special, unquoted_special)
        assert special == unquoted_special

class TestPOUnit(test_base.TestTranslationUnit):
    UnitClass = po.pounit
    def test_istranslatable(self):
        """Tests for the correct behaviour of istranslatable()."""
        unit = self.UnitClass("Message")
        assert unit.istranslatable()

        unit.source = " "
        assert unit.istranslatable()

        unit.source = ""
        assert not unit.istranslatable()
        # simulate a header
        unit.target = "PO-Revision-Date: 2006-02-09 23:33+0200\n"
        assert unit.isheader()
        assert not unit.istranslatable()

        unit.source = "Message"
        unit.target = "Boodskap"
        unit.makeobsolete()
        assert not unit.istranslatable()

    def test_adding_empty_note(self):
        unit = self.UnitClass("bla")
        assert not '#' in str(unit)
        for empty_string in [ "", " ", "\t", "\n" ]:
            unit.addnote(empty_string)
            assert not '#' in str(unit)

    def test_markreview(self):
        """Tests if we can mark the unit to need review."""
        unit = self.unit
        # We have to explicitly set the target to nothing, otherwise xliff
        # tests will fail.
        # Can we make it default behavior for the UnitClass?
        unit.target = ""

        unit.addnote("Test note 1", origin="translator")
        unit.addnote("Test note 2", origin="translator")
        original_notes = unit.getnotes(origin="translator")

        assert not unit.isreview()
        unit.markreviewneeded()
        print unit.getnotes()
        assert unit.isreview()
        unit.markreviewneeded(False)
        assert not unit.isreview()
        assert unit.getnotes(origin="translator") == original_notes
        unit.markreviewneeded(explanation="Double check spelling.")
        assert unit.isreview()
        notes = unit.getnotes(origin="translator")
        assert notes.count("Double check spelling.") == 1

    def test_errors(self):
        """Tests that we can add and retrieve error messages for a unit."""
        unit = self.unit

        assert len(unit.geterrors()) == 0
        unit.adderror(errorname='test1', errortext='Test error message 1.')
        unit.adderror(errorname='test2', errortext='Test error message 2.')
        unit.adderror(errorname='test3', errortext='Test error message 3.')
        assert len(unit.geterrors()) == 3
        assert unit.geterrors()['test1'] == 'Test error message 1.'
        assert unit.geterrors()['test2'] == 'Test error message 2.'
        assert unit.geterrors()['test3'] == 'Test error message 3.'
        unit.adderror(errorname='test1', errortext='New error 1.')
        assert unit.geterrors()['test1'] == 'New error 1.'

    def test_no_plural_settarget(self):
        """tests that target handling of file with no plural is correct"""
        # plain text, no plural test
        unit = self.UnitClass("Tree")
        unit.target = "ki"
        assert unit.hasplural() == False

        # plural test with multistring
        unit.setsource(["Tree", "Trees"])
        assert unit.source.strings == ["Tree", "Trees"]
        assert unit.hasplural()
        unit.target = multistring(["ki", "ni ki"])
        assert unit.target.strings == ["ki", "ni ki"]

        # test of msgid with no plural and msgstr with plural
        unit = self.UnitClass("Tree")
        assert raises(ValueError, unit.settarget, [u"ki", u"ni ki"])
        assert unit.hasplural() == False

    def test_wrapping_bug(self):
        """This tests for a wrapping bug that existed at some stage."""
        unit = self.UnitClass("")
        message = 'Projeke ya Pootle ka boyona e ho <a href="http://translate.sourceforge.net/">translate.sourceforge.net</a> moo o ka fumanang dintlha ka source code, di mailing list jwalo jwalo.'
        unit.target = message
        print unit.target
        assert unit.target == message

    def test_extract_msgidcomments_from_text(self):
        """Test that KDE style comments are extracted correctly."""
        unit = self.UnitClass("test source")

        kdetext = "_: Simple comment\nsimple text"
        assert unit._extract_msgidcomments(kdetext) == "Simple comment"

    def test_isheader(self):
        """checks that we deal correctly with headers."""
        unit = self.UnitClass()
        unit.target = "PO-Revision-Date: 2006-02-09 23:33+0200\n"
        assert unit.isheader()
        unit.source = "Some English string"
        assert not unit.isheader()
        unit.source = u"Goeiemôre"
        assert not unit.isheader()

#     def test_rich_source(self):
#         unit = self.unit
#         unit.rich_source = [['a', X('42'), 'c']]
#         assert unit.rich_source == [[u'a\ufffcc']]

#     def test_rich_target(self):
#         unit = self.unit
#         unit.rich_target = [['a', G('42', ['b']), 'c']]
#         assert unit.rich_target == [['abc']]

class TestPOFile(test_base.TestTranslationStore):
    StoreClass = po.pofile
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = self.StoreClass(dummyfile)
        return pofile

    def poregen(self, posource):
        """helper that converts po source to pofile object and back"""
        return str(self.poparse(posource))

    def pomerge(self, oldmessage, newmessage, authoritative):
        """helper that merges two messages"""
        oldpofile = self.poparse(oldmessage)
        oldunit = oldpofile.units[0]
        if newmessage:
            newpofile = self.poparse(newmessage)
            newunit = newpofile.units[0]
        else:
            newunit = oldpofile.UnitClass()
        oldunit.merge(newunit, authoritative=authoritative)
        print oldunit
        return str(oldunit)

    def test_context_only(self):
        """Checks that an empty msgid with msgctxt is handled correctly."""
        posource = '''msgctxt "CONTEXT"
msgid ""
msgstr ""
'''
        pofile = self.poparse(posource)
        assert pofile.units[0].istranslatable()
        assert not pofile.units[0].isheader()
        # we were not generating output for thse at some stage
        assert str(pofile)

    def test_simpleentry(self):
        """checks that a simple po entry is parsed correctly"""
        posource = '#: test.c:100 test.c:101\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1
        thepo = pofile.units[0]
        assert thepo.getlocations() == ["test.c:100", "test.c:101"]
        assert thepo.source == "test"
        assert thepo.target == "rest"

    def test_copy(self):
        """checks that we can copy all the needed PO fields"""
        posource = '''# TRANSLATOR-COMMENTS
#. AUTOMATIC-COMMENTS
#: REFERENCE...
#, fuzzy
msgctxt "CONTEXT"
msgid "UNTRANSLATED-STRING"
msgstr "TRANSLATED-STRING"'''
        pofile = self.poparse(posource)
        oldunit = pofile.units[0]
        newunit = oldunit.copy()
        assert newunit == oldunit

    def test_parse_source_string(self):
        """parse a string"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1

    def test_parse_file(self):
        """test parsing a real file"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1

    def test_unicode(self):
        """check that the po class can handle Unicode characters"""
        posource = 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n#: test.c\nmsgid "test"\nmsgstr "rest\xe2\x80\xa6"\n'
        pofile = self.poparse(posource)
        print pofile
        assert len(pofile.units) == 2

    def test_plurals(self):
        posource = r'''msgid "Cow"
msgid_plural "Cows"
msgstr[0] "Koei"
msgstr[1] "Koeie"
'''
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert isinstance(unit.target, multistring)
        print unit.target.strings
        assert unit.target == "Koei"
        assert unit.target.strings == ["Koei", "Koeie"]

        posource = r'''msgid "Skaap"
msgid_plural "Skape"
msgstr[0] "Sheep"
'''
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert isinstance(unit.target, multistring)
        print unit.target.strings
        assert unit.target == "Sheep"
        assert unit.target.strings == ["Sheep"]

    def test_plural_unicode(self):
        """tests that all parts of the multistring are unicode."""
        posource = r'''msgid "Ców"
msgid_plural "Cóws"
msgstr[0] "Kóei"
msgstr[1] "Kóeie"
'''
        pofile = self.poparse(posource)
        unit = pofile.units[0]
        assert isinstance(unit.source, multistring)
        assert isinstance(unit.source.strings[1], unicode)


    def wtest_kde_plurals(self):
        """Tests kde-style plurals. (Bug: 191)"""
        posource = '''msgid "_n Singular\n"
"Plural"
msgstr "Een\n"
"Twee\n"
"Drie"
'''
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert unit.hasplural() == True
        assert isinstance(unit.source, multistring)
        print unit.source.strings
        assert unit.source == "Singular"
        assert unit.source.strings == ["Singular", "Plural"]
        assert isinstance(unit.target, multistring)
        print unit.target.strings
        assert unit.target == "Een"
        assert unit.target.strings == ["Een", "Twee", "Drie"]

    def test_empty_lines_notes(self):
        """Tests that empty comment lines are preserved"""
        posource = r'''# License name
#
# license line 1
# license line 2
# license line 3
msgid ""
msgstr "POT-Creation-Date: 2006-03-08 17:30+0200\n"
'''
        pofile = self.poparse(posource)
        assert str(pofile) == posource

    def test_fuzzy(self):
        """checks that fuzzy functionality works as expected"""
        posource = '#, fuzzy\nmsgid "ball"\nmsgstr "bal"\n'
        expectednonfuzzy = 'msgid "ball"\nmsgstr "bal"\n'
        pofile = self.poparse(posource)
        print pofile
        assert pofile.units[0].isfuzzy()
        pofile.units[0].markfuzzy(False)
        assert not pofile.units[0].isfuzzy()
        assert str(pofile) == expectednonfuzzy

        posource = '#, fuzzy, python-format\nmsgid "ball"\nmsgstr "bal"\n'
        expectednonfuzzy = '#, python-format\nmsgid "ball"\nmsgstr "bal"\n'
        pofile = self.poparse(posource)
        print pofile
        assert pofile.units[0].isfuzzy()
        pofile.units[0].markfuzzy(False)
        assert not pofile.units[0].isfuzzy()
        assert str(pofile) == expectednonfuzzy

    def xtest_makeobsolete_untranslated(self):
        """Tests making an untranslated unit obsolete"""
        posource = '#. The automatic one\n#: test.c\nmsgid "test"\nmsgstr ""\n'
        pofile = self.poparse(posource)
        unit = pofile.units[0]
        assert not unit.isobsolete()
        unit.makeobsolete()
        assert str(unit) == ""
        # a better way might be for pomerge/pot2po to remove the unit

    def test_merging_automaticcomments(self):
        """checks that new automatic comments override old ones"""
        oldsource = '#. old comment\n#: line:10\nmsgid "One"\nmsgstr "Een"\n'
        newsource = '#. new comment\n#: line:10\nmsgid "One"\nmsgstr ""\n'
        expected = '#. new comment\n#: line:10\nmsgid "One"\nmsgstr "Een"\n'
        assert self.pomerge(newsource, oldsource, authoritative=True) == expected

    def test_malformed_units(self):
        """Test that we handle malformed units reasonably."""
        posource = 'msgid "thing\nmsgstr "ding"\nmsgid "Second thing"\nmsgstr "Tweede ding"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        print `pofile.units[0].source`
        assert pofile.units[0].source == u"thing"

    def test_malformed_obsolete_units(self):
        """Test that we handle malformed obsolete units reasonably."""
        posource = '''msgid "thing
msgstr "ding"

#~ msgid "Second thing"
#~ msgstr "Tweede ding"
#~ msgid "Third thing"
#~ msgstr "Derde ding"
'''
        pofile = self.poparse(posource)
        assert len(pofile.units) == 3

    def test_uniforum_po(self):
        """Test that we handle Uniforum PO files."""
        posource = '''# File: ../somefile.cpp, line: 33
msgid "thing"
msgstr "ding"
#
# File: anotherfile.cpp, line: 34
msgid "second"
msgstr "tweede"
'''
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        # FIXME we still need to handle this correctly for proper Uniforum support if required
        #assert pofile.units[0].getlocations() == "File: somefile, line: 300"
        #assert pofile.units[1].getlocations() == "File: anotherfile, line: 200"

    def test_obsolete(self):
        """Tests that obsolete messages work"""
        posource = '#~ msgid "Old thing"\n#~ msgstr "Ou ding"\n'
        pofile = self.poparse(posource)
        assert pofile.isempty()
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert unit.isobsolete()
        assert str(pofile) == posource

        posource = '''msgid "one"
msgstr "een"

#, fuzzy
#~ msgid "File not found."
#~ msgid_plural "Files not found."
#~ msgstr[0] "Leer(s) nie gevind nie."
#~ msgstr[1] "Leer(s) nie gevind nie."
'''
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        unit = pofile.units[1]
        assert unit.isobsolete()

        print str(pofile)
        assert str(pofile) == posource
        unit.resurrect()
        assert unit.hasplural()


    def test_header_escapes(self):
        pofile = self.StoreClass()
        pofile.updateheader(add=True, **{"Report-Msgid-Bugs-To": r"http://qa.openoffice.org/issues/enter_bug.cgi?subcomponent=ui&comment=&short_desc=Localization%20issue%20in%20file%3A%20dbaccess\source\core\resource.oo&component=l10n&form_name=enter_issue"})
        filecontents = str(pofile)
        print filecontents
        # We need to make sure that the \r didn't get misrepresented as a 
        # carriage return, but as a slash (escaped) followed by a normal 'r'
        assert r'\source\core\resource' in pofile.header().target
        assert r're\\resource' in filecontents

    def test_makeobsolete(self):
        """Tests making a unit obsolete"""
        posource = '#. The automatic one\n#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poexpected = '#~ msgid "test"\n#~ msgstr "rest"\n'
        pofile = self.poparse(posource)
        print pofile
        unit = pofile.units[0]
        assert not unit.isobsolete()
        unit.makeobsolete()
        assert unit.isobsolete()
        print pofile
        assert str(unit) == poexpected

    def test_makeobsolete_plural(self):
        """Tests making a plural unit obsolete"""
        posource = r'''msgid "Cow"
msgid_plural "Cows"
msgstr[0] "Koei"
msgstr[1] "Koeie"
'''
        poexpected = '''#~ msgid "Cow"
#~ msgid_plural "Cows"
#~ msgstr[0] "Koei"
#~ msgstr[1] "Koeie"
'''
        pofile = self.poparse(posource)
        print pofile
        unit = pofile.units[0]
        assert not unit.isobsolete()
        unit.makeobsolete()
        assert unit.isobsolete()
        print pofile
        assert str(unit) == poexpected


    def test_makeobsolete_msgctxt(self):
        """Tests making a unit with msgctxt obsolete"""
        posource = '#: test.c\nmsgctxt "Context"\nmsgid "test"\nmsgstr "rest"\n'
        poexpected = '#~ msgctxt "Context"\n#~ msgid "test"\n#~ msgstr "rest"\n'
        pofile = self.poparse(posource)
        print pofile
        unit = pofile.units[0]
        assert not unit.isobsolete()
        assert unit.istranslatable()
        unit.makeobsolete()
        assert unit.isobsolete()
        assert not unit.istranslatable()
        print pofile
        assert str(unit) == poexpected

    def test_makeobsolete_msgidcomments(self):
        """Tests making a unit with msgidcomments obsolete"""
        posource = '#: first.c\nmsgid ""\n"_: first.c\\n"\n"test"\nmsgstr "rest"\n\n#: second.c\nmsgid ""\n"_: second.c\\n"\n"test"\nmsgstr "rest"'
        poexpected = '#~ msgid ""\n#~ "_: first.c\\n"\n#~ "test"\n#~ msgstr "rest"\n'
        print "Source:\n%s" % posource
        print "Expected:\n%s" % poexpected
        pofile = self.poparse(posource)
        unit = pofile.units[0]
        assert not unit.isobsolete()
        unit.makeobsolete()
        assert unit.isobsolete()
        print "Result:\n%s" % pofile
        assert str(unit) == poexpected

    def test_multiline_obsolete(self):
        """Tests for correct output of mulitline obsolete messages"""
        posource = '#~ msgid ""\n#~ "Old thing\\n"\n#~ "Second old thing"\n#~ msgstr ""\n#~ "Ou ding\\n"\n#~ "Tweede ou ding"\n'
        pofile = self.poparse(posource)
        assert pofile.isempty()
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert unit.isobsolete()
        print str(pofile)
        print posource
        assert str(pofile) == posource

    def test_merge_duplicates(self):
        """checks that merging duplicates works"""
        posource = '#: source1\nmsgid "test me"\nmsgstr ""\n\n#: source2\nmsgid "test me"\nmsgstr ""\n'
        pofile = self.poparse(posource)
        #assert len(pofile.units) == 2
        pofile.removeduplicates("merge")
        assert len(pofile.units) == 1
        assert pofile.units[0].getlocations() == ["source1", "source2"]
        print pofile

    def test_merge_mixed_sources(self):
        """checks that merging works with different source location styles"""
        posource = '''
#: source1
#: source2
msgid "test"
msgstr ""

#: source1 source2
msgid "test"
msgstr ""
'''
        pofile = self.poparse(posource)
        print str(pofile)
        pofile.removeduplicates("merge")
        print str(pofile)
        assert len(pofile.units) == 1
        assert pofile.units[0].getlocations() == ["source1", "source2"]

    def test_parse_context(self):
        """Tests that msgctxt is parsed correctly and that it is accessible via the api methods."""
        posource = '''# Test comment
#: source1
msgctxt "noun"
msgid "convert"
msgstr "bekeerling"

# Test comment 2
#: source2
msgctxt "verb"
msgid "convert"
msgstr "omskakel"
'''
        pofile = self.poparse(posource)
        unit = pofile.units[0]

        assert unit.getcontext() == 'noun'
        assert unit.getnotes() == 'Test comment'

        unit = pofile.units[1]
        assert unit.getcontext() == 'verb'
        assert unit.getnotes() == 'Test comment 2'

    def test_parse_advanced_context(self):
        """Tests that some weird possible msgctxt scenarios are parsed correctly."""
        posource = r'''# Test multiline context
#: source1
msgctxt "Noun."
" A person that changes his or her ways."
msgid "convert"
msgstr "bekeerling"

# Test quotes
#: source2
msgctxt "Verb. Converting from \"something\" to \"something else\"."
msgid "convert"
msgstr "omskakel"

# Test quotes, newlines and multiline.
#: source3
msgctxt "Verb.\nConverting from \"something\""
" to \"something else\"."
msgid "convert"
msgstr "omskakel"
'''
        pofile = self.poparse(posource)
        unit = pofile.units[0]

        assert unit.getcontext() == 'Noun. A person that changes his or her ways.'
        assert unit.getnotes() == 'Test multiline context'

        unit = pofile.units[1]
        assert unit.getcontext() == 'Verb. Converting from "something" to "something else".'
        assert unit.getnotes() == 'Test quotes'

        unit = pofile.units[2]
        assert unit.getcontext() == 'Verb.\nConverting from "something" to "something else".'
        assert unit.getnotes() == 'Test quotes, newlines and multiline.'

    def test_kde_context(self):
        """Tests that kde-style msgid comments can be retrieved via getcontext()."""
        posource = '''# Test comment
#: source1
msgid ""
"_: Noun\\n"
"convert"
msgstr "bekeerling"

# Test comment 2
#: source2
msgid ""
"_: Verb. _: "
"The action of changing.\\n"
"convert"
msgstr "omskakel"
'''
        pofile = self.poparse(posource)
        unit = pofile.units[0]

        assert unit.getcontext() == 'Noun'
        assert unit.getnotes() == 'Test comment'

        unit = pofile.units[1]
        assert unit.getcontext() == 'Verb. _: The action of changing.'
        assert unit.getnotes() == 'Test comment 2'

    def test_broken_kde_context(self):
        posource = '''msgid "Broken _: here"
msgstr "Broken _: here"
'''
        pofile = self.poparse(posource)
        unit = pofile.units[0]
        assert unit.source == "Broken _: here"
        assert unit.target == "Broken _: here"

    def test_id(self):
        """checks that ids work correctly"""
        posource = r'''
msgid ""
msgstr ""
"PO-Revision-Date: 2006-02-09 23:33+0200\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8-bit\n"

msgid "plant"
msgstr ""

msgid ""
"_: Noun\n"
"convert"
msgstr "bekeerling"

msgctxt "verb"
msgid ""
"convert"
msgstr "omskakel"

msgid "tree"
msgid_plural "trees"
msgstr[0] ""
'''
        pofile = self.poparse(posource)
        assert pofile.units[0].getid() == ""
        assert pofile.units[1].getid() == "plant"
        assert pofile.units[2].getid() == "_: Noun\nconvert"
        assert pofile.units[3].getid() == "verb\04convert"
        # Gettext does not consider the plural to determine duplicates, only
        # the msgid. For generation of .mo files, we might want to use this
        # code to generate the entry for the hash table, but for now, it is
        # commented out for conformance to gettext.
#        assert pofile.units[4].getid() == "tree\0trees"

    def test_non_ascii_header_comments(self):
        posource = r'''
# Tëśt þis.
# Hé Há Hó.
#. Lêkkør.
msgid ""
msgstr ""
"PO-Revision-Date: 2006-02-09 23:33+0200\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8-bit\n"

msgid "a"
msgstr "b"
'''
        pofile = self.poparse(posource)
        for line in pofile.units[0].getnotes():
            assert isinstance(line, unicode)

    def test_final_slash(self):
        """Test that \ as last character is correcly interpreted (bug 960)."""
        posource = r'''
msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\n"

#: System-Support,Project>>decideAboutCreatingBlank:
msgid "I cannot locate the project\\"
msgstr "プロジェクトが見つかりませんでした"
'''
        pofile1 = self.poparse(posource)
        print pofile1.units[1].source
        assert pofile1.units[1].source == u"I cannot locate the project\\"
        pofile2 = self.poparse(str(pofile1))
        print str(pofile2)
        assert str(pofile1) == str(pofile2)

    def test_unfinished_lines(self):
        """Test that we reasonably handle lines with a single quote."""
        posource = r'''
msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\n"

msgid "I cannot locate the project\\"
msgstr "start thing dingis fish"
"
"
'''
        pofile1 = self.poparse(posource)
        print `pofile1.units[1].target`
        assert pofile1.units[1].target == u"start thing dingis fish"
        pofile2 = self.poparse(str(pofile1))
        assert pofile2.units[1].target == u"start thing dingis fish"
        print str(pofile2)
        assert str(pofile1) == str(pofile2)
