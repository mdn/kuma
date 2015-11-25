#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from pytest import mark

from translate.misc import wStringIO
from translate.storage import po, xliff
from translate.tools import pomerge


def test_str2bool():
    """test the str2bool function"""
    assert pomerge.str2bool("yes")
    assert pomerge.str2bool("true")
    assert pomerge.str2bool("1")
    assert not pomerge.str2bool("no")
    assert not pomerge.str2bool("false")
    assert not pomerge.str2bool("0")
    pytest.raises(ValueError, pomerge.str2bool, "2")


class TestPOMerge:
    xliffskeleton = '''<?xml version="1.0" ?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
  <file original="filename.po" source-language="en-US" datatype="po">
    <body>
        %s
    </body>
  </file>
</xliff>'''

    def mergestore(self, templatesource, inputsource, mergeblanks="yes",
                   mergefuzzy="yes",
                   mergecomments="yes"):
        """merges the sources of the given files and returns a new pofile
        object"""
        templatefile = wStringIO.StringIO(templatesource)
        inputfile = wStringIO.StringIO(inputsource)
        outputfile = wStringIO.StringIO()
        assert pomerge.mergestore(inputfile, outputfile, templatefile,
                                  mergeblanks=mergeblanks,
                                  mergefuzzy=mergefuzzy,
                                  mergecomments=mergecomments,)
        outputpostring = outputfile.getvalue()
        outputpofile = po.pofile(outputpostring)
        return outputpofile

    def mergexliff(self, templatesource, inputsource, mergeblanks="yes",
                   mergefuzzy="yes",
                   mergecomments="yes"):
        """merges the sources of the given files and returns a new xlifffile
        object"""
        templatefile = wStringIO.StringIO(templatesource)
        inputfile = wStringIO.StringIO(inputsource)
        outputfile = wStringIO.StringIO()
        assert pomerge.mergestore(inputfile, outputfile, templatefile,
                                  mergeblanks=mergeblanks,
                                  mergefuzzy=mergefuzzy,
                                  mergecomments=mergecomments)
        outputxliffstring = outputfile.getvalue()
        print("Generated XML:")
        print(outputxliffstring)
        outputxlifffile = xliff.xlifffile(outputxliffstring)
        return outputxlifffile

    def countunits(self, pofile):
        """returns the number of non-header items"""
        if pofile.units[0].isheader():
            return len(pofile.units) - 1
        else:
            return len(pofile.units)

    def singleunit(self, pofile):
        """checks that the pofile contains a single non-header unit, and
        returns it"""
        assert self.countunits(pofile) == 1
        return pofile.units[-1]

    def test_mergesore_bad_data(self):
        """Test that we catch bad options sent to mergestore"""
        templatefile = wStringIO.StringIO("")
        inputfile = wStringIO.StringIO("")
        outputfile = wStringIO.StringIO()
        pytest.raises(ValueError, pomerge.mergestore, inputfile, outputfile,
                    templatefile, mergeblanks="yay")
        pytest.raises(ValueError, pomerge.mergestore, inputfile, outputfile,
                    templatefile, mergecomments="yay")

    def test_simplemerge(self):
        """checks that a simple po entry merges OK"""
        templatepo = '''#: simple.test\nmsgid "Simple String"\nmsgstr ""\n'''
        inputpo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        pofile = self.mergestore(templatepo, inputpo)
        pounit = self.singleunit(pofile)
        assert pounit.source == "Simple String"
        assert pounit.target == "Dimpled Ring"

    def test_simplemerge_no_locations(self):
        """checks that a simple po entry merges OK"""
        templatepo = '''msgid "Simple String"
msgstr ""'''
        inputpo = '''msgid "Simple String"
msgstr "Dimpled Ring"'''
        pofile = self.mergestore(templatepo, inputpo)
        pounit = self.singleunit(pofile)
        assert pounit.source == "Simple String"
        assert pounit.target == "Dimpled Ring"

    def test_replacemerge(self):
        """checks that a simple po entry merges OK"""
        templatepo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        inputpo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled King"\n'''
        pofile = self.mergestore(templatepo, inputpo)
        pounit = self.singleunit(pofile)
        assert pounit.source == "Simple String"
        assert pounit.target == "Dimpled King"

    def test_merging_blanks(self):
        """By default we will merge blanks, but we can also override that"""
        templatepo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        inputpo = '''#: simple.test\nmsgid "Simple String"\nmsgstr ""\n'''
        pofile = self.mergestore(templatepo, inputpo)
        pounit = self.singleunit(pofile)
        assert pounit.source == "Simple String"
        assert pounit.target == ""
        pofile = self.mergestore(templatepo, inputpo, mergeblanks="no")
        pounit = self.singleunit(pofile)
        assert pounit.source == "Simple String"
        assert pounit.target == "Dimpled Ring"

    def test_merging_fuzzies(self):
        """By default we will merge fuzzies, but can can also override that."""
        templatepo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        inputpo = '''#: simple.test\n#, fuzzy\nmsgid "Simple String"\nmsgstr "changed fish"\n'''
        pofile = self.mergestore(templatepo, inputpo)
        pounit = self.singleunit(pofile)
        assert pounit.source == "Simple String"
        assert pounit.target == "changed fish"
        assert pounit.isfuzzy()
        pofile = self.mergestore(templatepo, inputpo, mergefuzzy="no")
        pounit = self.singleunit(pofile)
        assert pounit.source == "Simple String"
        assert pounit.target == "Dimpled Ring"
        assert not pounit.isfuzzy()

    def test_merging_locations(self):
        """check that locations on separate lines are output in Gettext form
        of all on one line"""
        templatepo = '''#: location.c:1\n#: location.c:2\nmsgid "Simple String"\nmsgstr ""\n'''
        inputpo = '''#: location.c:1\n#: location.c:2\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        expectedpo = '''#: location.c:1%slocation.c:2\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n''' % po.lsep
        pofile = self.mergestore(templatepo, inputpo)
        print(pofile)
        assert str(pofile) == expectedpo

    def test_unit_missing_in_template_with_locations(self):
        """If the unit is missing in the template we should raise an error"""
        templatepo = '''#: location.c:1
msgid "Simple String"
msgstr ""'''
        inputpo = '''#: location.c:1
msgid "Simple String"
msgstr "Dimpled Ring"

#: location.c:1
msgid "Extra string"
msgstr "Perplexa ring"'''
        expectedpo = '''#: location.c:1
msgid "Simple String"
msgstr "Dimpled Ring"
'''
        pofile = self.mergestore(templatepo, inputpo)
        print(pofile)
        assert str(pofile) == expectedpo

    def test_unit_missing_in_template_no_locations(self):
        """If the unit is missing in the template we should raise an error"""
        templatepo = '''msgid "Simple String"
msgstr ""'''
        inputpo = '''msgid "Simple String"
msgstr "Dimpled Ring"

msgid "Extra string"
msgstr "Perplexa ring"'''
        expectedpo = '''msgid "Simple String"
msgstr "Dimpled Ring"
'''
        pofile = self.mergestore(templatepo, inputpo)
        print(pofile)
        assert str(pofile) == expectedpo

    def test_reflowed_source_comments(self):
        """ensure that we don't duplicate source comments (locations) if they
        have been reflowed"""
        templatepo = '''#: newMenu.label\n#: newMenu.accesskey\nmsgid "&New"\nmsgstr ""\n'''
        newpo = '''#: newMenu.label newMenu.accesskey\nmsgid "&New"\nmsgstr "&Nuwe"\n'''
        expectedpo = '''#: newMenu.label%snewMenu.accesskey\nmsgid "&New"\nmsgstr "&Nuwe"\n''' % po.lsep
        pofile = self.mergestore(templatepo, newpo)
        pounit = self.singleunit(pofile)
        print(pofile)
        assert str(pofile) == expectedpo

    def test_comments_with_blank_lines(self):
        """ensure that we don't loose empty newlines in comments"""
        templatepo = '''# # ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# bla bla
msgid "bla"
msgstr "blabla"
'''
        newpo = templatepo
        expectedpo = templatepo
        pofile = self.mergestore(templatepo, newpo)
        pounit = self.singleunit(pofile)
        print(pofile)
        assert str(pofile) == expectedpo

    def test_merge_dont_delete_unassociated_comments(self):
        """ensure that we do not delete comments in the PO file that are not
        assocaited with a message block"""
        templatepo = '''# Lonely comment\n\n# Translation comment\nmsgid "Bob"\nmsgstr "Toolmaker"\n'''
        mergepo = '''# Translation comment\nmsgid "Bob"\nmsgstr "Builder"\n'''
        expectedpo = '''# Lonely comment\n# Translation comment\nmsgid "Bob"\nmsgstr "Builder"\n'''
        pofile = self.mergestore(templatepo, mergepo)
#        pounit = self.singleunit(pofile)
        print(pofile)
        assert str(pofile) == expectedpo

    def test_preserve_format_trailing_newlines(self):
        """Test that we can merge messages correctly that end with a newline"""
        templatepo = '''msgid "Simple string\\n"\nmsgstr ""\n'''
        mergepo = '''msgid "Simple string\\n"\nmsgstr "Dimpled ring\\n"\n'''
        expectedpo = '''msgid "Simple string\\n"\nmsgstr "Dimpled ring\\n"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

        templatepo = '''msgid ""\n"Simple string\\n"\nmsgstr ""\n'''
        mergepo = '''msgid ""\n"Simple string\\n"\nmsgstr ""\n"Dimpled ring\\n"\n'''
        expectedpo = '''msgid ""\n"Simple string\\n"\nmsgstr "Dimpled ring\\n"\n'''
        expectedpo2 = '''msgid "Simple string\\n"\nmsgstr "Dimpled ring\\n"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo or str(pofile) == expectedpo2

    def test_preserve_format_minor_start_and_end_of_sentence_changes(self):
        """Test that we are not too fussy about large diffs for simple
        changes at the start or end of a sentence"""
        templatepo = '''msgid "Target type:"\nmsgstr "Doelsoort"\n\n'''
        mergepo = '''msgid "Target type:"\nmsgstr "Doelsoort:"\n'''
        expectedpo = mergepo
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

        templatepo = '''msgid "&Select"\nmsgstr "Kies"\n\n'''
        mergepo = '''msgid "&Select"\nmsgstr "&Kies"\n'''
        expectedpo = mergepo
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

        templatepo = '''msgid "en-us, en"\nmsgstr "en-us, en"\n'''
        mergepo = '''msgid "en-us, en"\nmsgstr "af-za, af, en-za, en-gb, en-us, en"\n'''
        expectedpo = mergepo
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

    def test_preserve_format_last_entry_in_a_file(self):
        """The last entry in a PO file is usualy not followed by an empty
        line.  Test that we preserve this"""
        templatepo = '''msgid "First"\nmsgstr ""\n\nmsgid "Second"\nmsgstr ""\n'''
        mergepo = '''msgid "First"\nmsgstr "Eerste"\n\nmsgid "Second"\nmsgstr "Tweede"\n'''
        expectedpo = '''msgid "First"\nmsgstr "Eerste"\n\nmsgid "Second"\nmsgstr "Tweede"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

        templatepo = '''msgid "First"\nmsgstr ""\n\nmsgid "Second"\nmsgstr ""\n\n'''
        mergepo = '''msgid "First"\nmsgstr "Eerste"\n\nmsgid "Second"\nmsgstr "Tweede"\n'''
        expectedpo = '''msgid "First"\nmsgstr "Eerste"\n\nmsgid "Second"\nmsgstr "Tweede"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

    @mark.xfail(reason="Not Implemented")
    def test_escape_tabs(self):
        """Ensure that input tabs are escaped in the output, like
        gettext does."""

        # The strings below contains the tab character, not spaces.
        templatepo = '''msgid "First	Second"\nmsgstr ""\n\n'''
        mergepo = '''msgid "First	Second"\nmsgstr "Eerste	Tweede"\n'''
        expectedpo = r'''msgid "First\tSecond"
msgstr "Eerste\tTweede"
'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

    def test_preserve_comments_layout(self):
        """Ensure that when we merge with new '# (poconflict)' or other
        comments that we don't mess formating"""
        templatepo = '''#: filename\nmsgid "Desktop Background.bmp"\nmsgstr "Desktop Background.bmp"\n\n'''
        mergepo = '''# (pofilter) unchanged: please translate\n#: filename\nmsgid "Desktop Background.bmp"\nmsgstr "Desktop Background.bmp"\n'''
        expectedpo = mergepo
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

    def test_merge_dos2unix(self):
        """Test that merging a comment line with dos newlines doesn't add a
        new line"""
        templatepo = '''# User comment\n# (pofilter) Translate Toolkit comment\n#. Automatic comment\n#: location_comment.c:110\nmsgid "File"\nmsgstr "File"\n\n'''
        mergepo = '''# User comment\r\n# (pofilter) Translate Toolkit comment\r\n#. Automatic comment\r\n#: location_comment.c:110\r\nmsgid "File"\r\nmsgstr "Ifayile"\r\n\r\n'''
        expectedpo = '''# User comment\n# (pofilter) Translate Toolkit comment\n#. Automatic comment\n#: location_comment.c:110\nmsgid "File"\nmsgstr "Ifayile"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        assert str(pofile) == expectedpo

        # Unassociated comment
        templatepo = '''# Lonely comment\n\n#: location_comment.c:110\nmsgid "Bob"\nmsgstr "Toolmaker"\n'''
        mergepo = '''# Lonely comment\r\n\r\n#: location_comment.c:110\r\nmsgid "Bob"\r\nmsgstr "Builder"\r\n\r\n'''
        expectedpo = '''# Lonely comment\n#: location_comment.c:110\nmsgid "Bob"\nmsgstr "Builder"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        assert str(pofile) == expectedpo

        # New comment
        templatepo = '''#: location_comment.c:110\nmsgid "File"\nmsgstr "File"\n\n'''
        mergepo = '''# User comment\r\n# (pofilter) Translate Toolkit comment\r\n#: location_comment.c:110\r\nmsgid "File"\r\nmsgstr "Ifayile"\r\n\r\n'''
        expectedpo = '''# User comment\n# (pofilter) Translate Toolkit comment\n#: location_comment.c:110\nmsgid "File"\nmsgstr "Ifayile"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        assert str(pofile) == expectedpo

    def test_xliff_into_xliff(self):
        templatexliff = self.xliffskeleton % '''<trans-unit>
        <source>red</source>
        <target></target>
</trans-unit>'''
        mergexliff = self.xliffskeleton % '''<trans-unit>
        <source>red</source>
        <target>rooi</target>
</trans-unit>'''
        xlifffile = self.mergexliff(templatexliff, mergexliff)
        assert len(xlifffile.units) == 1
        unit = xlifffile.units[0]
        assert unit.source == "red"
        assert unit.target == "rooi"

    def test_po_into_xliff(self):
        templatexliff = self.xliffskeleton % '''<trans-unit>
        <source>red</source>
        <target></target>
</trans-unit>'''
        mergepo = 'msgid "red"\nmsgstr "rooi"'
        xlifffile = self.mergexliff(templatexliff, mergepo)
        assert len(xlifffile.units) == 1
        unit = xlifffile.units[0]
        assert unit.source == "red"
        assert unit.target == "rooi"

    def test_xliff_into_po(self):
        templatepo = '# my comment\nmsgid "red"\nmsgstr ""'
        mergexliff = self.xliffskeleton % '''<trans-unit>
        <source>red</source>
        <target>rooi</target>
</trans-unit>'''
        expectedpo = '# my comment\nmsgid "red"\nmsgstr "rooi"\n'
        pofile = self.mergestore(templatepo, mergexliff)
        assert str(pofile) == expectedpo

    def test_merging_dont_merge_kde_comments_found_in_translation(self):
        """If we find a KDE comment in the translation (target) then do not
        merge it."""

        templatepo = '''msgid "_: KDE comment\\n"\n"File"\nmsgstr "File"\n\n'''
        mergepo = '''msgid "_: KDE comment\\n"\n"File"\nmsgstr "_: KDE comment\\n"\n"Ifayile"\n\n'''
        expectedpo = '''msgid ""\n"_: KDE comment\\n"\n"File"\nmsgstr "Ifayile"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

        # Translated kde comment.
        mergepo = '''msgid "_: KDE comment\\n"\n"File"\nmsgstr "_: KDE kommentaar\\n"\n"Ifayile"\n\n'''
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

        # multiline KDE comment
        templatepo = '''msgid "_: KDE "\n"comment\\n"\n"File"\nmsgstr "File"\n\n'''
        mergepo = '''msgid "_: KDE "\n"comment\\n"\n"File"\nmsgstr "_: KDE "\n"comment\\n"\n"Ifayile"\n\n'''
        expectedpo = '''msgid ""\n"_: KDE comment\\n"\n"File"\nmsgstr "Ifayile"\n'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n\nMerged:\n%s" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

    def test_merging_untranslated_with_kde_disambiguation(self):
        """test merging untranslated messages that are the same except for
        KDE disambiguation"""
        templatepo = r'''#: sendMsgTitle
#: sendMsgTitle.accesskey
msgid "_: sendMsgTitle sendMsgTitle.accesskey\n"
"Send Message"
msgstr ""

#: sendMessageCheckWindowTitle
#: sendMessageCheckWindowTitle.accesskey
msgid "_: sendMessageCheckWindowTitle sendMessageCheckWindowTitle.accesskey\n"
"Send Message"
msgstr ""
'''
        mergepo = r'''#: sendMsgTitle%ssendMsgTitle.accesskey
msgid ""
"_: sendMsgTitle sendMsgTitle.accesskey\n"
"Send Message"
msgstr "Stuur"

#: sendMessageCheckWindowTitle%ssendMessageCheckWindowTitle.accesskey
msgid ""
"_: sendMessageCheckWindowTitle sendMessageCheckWindowTitle.accesskey\n"
"Send Message"
msgstr "Stuur"
''' % (po.lsep, po.lsep)
        expectedpo = mergepo
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n---\nMerged:\n%s\n---" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

    def test_merging_header_entries(self):
        """Check that we do the right thing if we have header entries in the
        input PO."""

        templatepo = r'''#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: new@example.com\n"
"POT-Creation-Date: 2006-11-11 11:11+0000\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\n"
"X-Generator: Translate Toolkit 0.10rc2\n"

#: simple.test
msgid "Simple String"
msgstr ""
'''
        mergepo = r'''msgid ""
msgstr ""
"Project-Id-Version: Pootle 0.10\n"
"Report-Msgid-Bugs-To: old@example.com\n"
"POT-Creation-Date: 2006-01-01 01:01+0100\n"
"PO-Revision-Date: 2006-09-09 09:09+0900\n"
"Last-Translator: Joe Translate <joe@example.com>\n"
"Language-Team: Pig Latin <piglatin@example.com>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"X-Generator: Translate Toolkit 0.9\n"

#: simple.test
msgid "Simple String"
msgstr "Dimpled Ring"
'''
        expectedpo = r'''msgid ""
msgstr ""
"Project-Id-Version: Pootle 0.10\n"
"Report-Msgid-Bugs-To: new@example.com\n"
"POT-Creation-Date: 2006-11-11 11:11+0000\n"
"PO-Revision-Date: 2006-09-09 09:09+0900\n"
"Last-Translator: Joe Translate <joe@example.com>\n"
"Language-Team: Pig Latin <piglatin@example.com>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"X-Generator: Translate Toolkit 0.10rc2\n"

#: simple.test
msgid "Simple String"
msgstr "Dimpled Ring"
'''
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n---\nMerged:\n%s\n---" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo

    def test_merging_different_locations(self):
        """Test when merging units that are unchanged except for changed
        locations that we don't go fuzzy (bug 1583)"""

        templatepo = r'''#, fuzzy
msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"

#: sentinelheadline
msgctxt "sentinelheadline"
msgid "DESTROY SENTINELS"
msgstr "ZERSTÖRE WACHPOSTEN"

#: sentinelheadline1
msgctxt "sentinelheadline1"
msgid "DESTROY SENTINELS"
msgstr "ZERSTÖRE WACHPOSTEN"
'''
        mergepo = r'''msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"

#: sentinelheadline
#: sentinelheadline1
msgctxt "sentinelheadline"
msgid "DESTROY SENTINELS"
msgstr "ZERSTÖRE WACHPOSTEN"

#: sentinelheadline1
msgctxt "sentinelheadline1"
msgid "DESTROY SENTINELS"
msgstr "ZERSTÖRE WACHPOSTEN"
'''
        expectedpo2 = r'''msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"

#: sentinelheadline sentinelheadline1
msgctxt "sentinelheadline"
msgid "DESTROY SENTINELS"
msgstr "ZERSTÖRE WACHPOSTEN"

#: sentinelheadline1
msgctxt "sentinelheadline1"
msgid "DESTROY SENTINELS"
msgstr "ZERSTÖRE WACHPOSTEN"
'''

        expectedpo = mergepo
        pofile = self.mergestore(templatepo, mergepo)
        print("Expected:\n%s\n---\nMerged:\n%s\n---" % (expectedpo, str(pofile)))
        assert str(pofile) == expectedpo or str(pofile) == expectedpo2
