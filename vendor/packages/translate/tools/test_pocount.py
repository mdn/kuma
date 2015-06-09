#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cStringIO import StringIO

from pytest import mark

from translate.storage import po, statsdb
from translate.tools import pocount


class TestCount:

    def count(self, source, expectedsource, target=None, expectedtarget=None):
        """simple helper to check the respective word counts"""
        poelement = po.pounit(source)
        if target is not None:
            poelement.target = target
        wordssource, wordstarget = statsdb.wordsinunit(poelement)
        print('Source (expected=%d; actual=%d): "%s"' % (expectedsource, wordssource, source))
        assert wordssource == expectedsource
        if target is not None:
            print('Target (expected=%d; actual=%d): "%s"' % (expectedtarget, wordstarget, target))
            assert wordstarget == expectedtarget

    def test_simple_count_zero(self):
        """no content"""
        self.count("", 0)

    def test_simple_count_one(self):
        """simplest one word count"""
        self.count("One", 1)

    def test_simple_count_two(self):
        """simplest one word count"""
        self.count("One two", 2)

    def test_punctuation_divides_words(self):
        """test that we break words when there is punctuation"""
        self.count("One. Two", 2)
        self.count("One.Two", 2)

    def test_xml_tags(self):
        """test that we do not count XML tags as words"""
        # <br> is a word break
        self.count("A word<br>Another word", 4)
        self.count("A word<br/>Another word", 4)
        self.count("A word<br />Another word", 4)
        # \n is a word break
        self.count("<p>A word</p>\n<p>Another word</p>", 4)
        # Not really an XML tag
        self.count("<no label>", 2)

    def test_newlines(self):
        """test to see that newlines divide words"""
        # newlines break words
        self.count("A word.\nAnother word", 4)
        self.count(r"A word.\\n\nAnother word", 4)

    def test_variables_are_words(self):
        """test that we count variables as words"""
        self.count("%PROGRAMNAME %PROGRAM% %s $file $1", 5)

    def test_plurals(self):
        """test that we can handle plural PO elements"""
        # #: gdk-pixbuf/gdk-pixdata.c:430
        # #, c-format
        # msgid "failed to allocate image buffer of %u byte"
        # msgid_plural "failed to allocate image buffer of %u bytes"
        # msgstr[0] "e paletšwe go hwetša sešireletši sa seswantšho sa paete ya %u"
        # msgstr[1] "e paletšwe go hwetša sešireletši sa seswantšho sa dipaete tša %u"

    @mark.xfail(reason="Support commented out pending removal")
    def test_plurals_kde(self):
        """test that we correcly count old style KDE plurals"""
        self.count("_n: Singular\\n\nPlural", 2, "Een\\n\ntwee\\n\ndrie", 3)

    def test_msgid_blank(self):
        """counts a message id"""
        self.count("   ", 0)

    # Counting strings
    #  We need to check how we count strings also and if we call it translated or untranslated
    # ie an all spaces msgid should be translated if there are spaces in the msgstr

    # Make sure we don't count obsolete messages

    # Do we correctly identify a translated yet blank message?

    # Need to test that we can differentiate between fuzzy, translated and untranslated


class TestPOCount:
    """This only tests the old (memory-based) pocount method, not the current
    code based on statsdb."""

    inputdata = r'''
msgid "translated unit"
msgstr "translated unit"

#, fuzzy
msgid "fuzzy unit"
msgstr "fuzzy unit"

# untranslated
msgid "untranslated unit"
msgstr ""

# obsolete
#~ msgid "obsolete translated unit"
#~ msgstr "obsolete translated unit"

#, fuzzy
#~ msgid "obsolete fuzzy unit"
#~ msgstr "obsolete fuzzy unit"

# untranslated
#~ msgid "obsolete untranslated unit"
#~ msgstr ""
'''

    def test_translated(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['translated'] == 1

    def test_fuzzy(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['fuzzy'] == 1

    def test_untranslated(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['untranslated'] == 1

    def test_total(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['total'] == 3

    def test_translatedsourcewords(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['translatedsourcewords'] == 2

    def test_fuzzysourcewords(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['fuzzysourcewords'] == 2

    def test_untranslatedsourcewords(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['untranslatedsourcewords'] == 2

    def test_totalsourcewords(self):
        pofile = StringIO(self.inputdata)
        stats = pocount.calcstats_old(pofile)
        assert stats['totalsourcewords'] == 6
