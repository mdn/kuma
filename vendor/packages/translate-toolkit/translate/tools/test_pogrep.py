#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import po
from translate.storage import xliff
from translate.storage.test_base import first_translatable, headerless_len
from translate.tools import pogrep
from translate.misc import wStringIO

class TestPOGrep:
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile)
        return pofile

    def pogrep(self, posource, searchstring, cmdlineoptions=None):
        """helper that parses po source and passes it through a filter"""
        if cmdlineoptions is None:
            cmdlineoptions = []
        options, args = pogrep.cmdlineparser().parse_args(["xxx.po"] + cmdlineoptions)
        grepfilter = pogrep.GrepFilter(searchstring, options.searchparts, options.ignorecase, options.useregexp, options.invertmatch, options.accelchar)
        tofile = grepfilter.filterfile(self.poparse(posource))
        print str(tofile)
        return str(tofile)

    def test_simplegrep_msgid(self):
        """grep for a string in the source"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poresult = self.pogrep(posource, "test", ["--search=msgid"])
        assert poresult.index(posource) >= 0
        poresult = self.pogrep(posource, "rest", ["--search=msgid"])
        assert headerless_len(po.pofile(poresult).units) == 0

    def test_simplegrep_msgstr(self):
        """grep for a string in the target"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poresult = self.pogrep(posource, "rest", ["--search=msgstr"])
        assert poresult.index(posource) >= 0
        poresult = self.pogrep(posource, "test", ["--search=msgstr"])
        assert headerless_len(po.pofile(poresult).units) == 0

    def test_simplegrep_locations(self):
        """grep for a string in the location comments"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poresult = self.pogrep(posource, "test.c", ["--search=locations"])
        assert poresult.index(posource) >= 0
        poresult = self.pogrep(posource, "rest.c", ["--search=locations"])
        assert headerless_len(po.pofile(poresult).units) == 0

    def test_simplegrep_comments(self):
        """grep for a string in the comments"""
        posource = '# (review) comment\n#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poresult = self.pogrep(posource, "review", ["--search=comment"])
        assert poresult.index(posource) >= 0
        poresult = self.pogrep(posource, "test", ["--search=comment"])
        assert headerless_len(po.pofile(poresult).units) == 0

    def test_simplegrep_locations_with_comment_enabled(self):
        """grep for a string in "locations", while also "comment" is checked
        see http://bugs.locamotion.org/show_bug.cgi?id=1036
        """
        posource = '# (review) comment\n#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poresult = self.pogrep(posource, "test", ["--search=comment", "--search=locations"])
        assert poresult.index(posource) >= 0
        poresult = self.pogrep(posource, "rest", ["--search=comment", "--search=locations"])
        assert headerless_len(po.pofile(poresult).units) == 0

    def test_unicode_message_searchstring(self):
        """check that we can grep unicode messages and use unicode search strings"""
        poascii = '# comment\n#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pounicode = '# comment\n#: test.c\nmsgid "test"\nmsgstr "rešṱ"\n'
        queryascii = 'rest'
        queryunicode = 'rešṱ'
        for source, search, expected in [(poascii, queryascii, poascii), 
                                         (poascii, queryunicode, ''),
                                         (pounicode, queryascii, ''),
                                         (pounicode, queryunicode, pounicode)]:
            print "Source:\n%s\nSearch: %s\n" % (source, search)
            poresult = self.pogrep(source, search)
            assert poresult.index(expected) >= 0

    def test_unicode_message_regex_searchstring(self):
        """check that we can grep unicode messages and use unicode regex search strings"""
        poascii = '# comment\n#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pounicode = '# comment\n#: test.c\nmsgid "test"\nmsgstr "rešṱ"\n'
        queryascii = 'rest'
        queryunicode = 'rešṱ'
        for source, search, expected in [(poascii, queryascii, poascii), 
                                         (poascii, queryunicode, ''),
                                         (pounicode, queryascii, ''),
                                         (pounicode, queryunicode, pounicode)]:
            print "Source:\n%s\nSearch: %s\n" % (source, search)
            poresult = self.pogrep(source, search, ["--regexp"])
            assert poresult.index(expected) >= 0

    def test_unicode_normalise(self):
        """check that we normlise unicode strings before comparing"""
        source_template = u'# comment\n#: test.c\nmsgid "test"\nmsgstr "t%sst"\n'
        # é, e + '
        # Ḽ, L + ^
        # Ṏ
        groups = [(u"\u00e9", u"\u0065\u0301"), \
                  (u"\u1e3c", u"\u004c\u032d"), \
                  (u"\u1e4e", u"\u004f\u0303\u0308", u"\u00d5\u0308")]
        for letters in groups:
            for source_letter in letters:
                source = source_template % source_letter
                for search_letter in letters:
                    print search_letter.encode('utf-8')
                    poresult = self.pogrep(source, search_letter)
                    assert poresult.index(source.encode('utf-8')) >= 0

class TestXLiffGrep:
    xliff_skeleton = '''<?xml version="1.0" ?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
  <file original="filename.po" source-language="en-US" datatype="po">
    <body>
        %s
    </body>
  </file>
</xliff>'''

    xliff_text = xliff_skeleton % '''<trans-unit>
  <source>rêd</source>
  <target>rooi</target>
</trans-unit>'''

    def xliff_parse(self, xliff_text):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(xliff_text)
        xliff_file = xliff.xlifffile(dummyfile)
        return xliff_file

    def xliff_grep(self, xliff_text, searchstring, cmdlineoptions=None):
        """helper that parses xliff text and passes it through a filter"""
        if cmdlineoptions is None:
            cmdlineoptions = []
        options, args = pogrep.cmdlineparser().parse_args(["xxx.xliff"] + cmdlineoptions)
        grepfilter = pogrep.GrepFilter(searchstring, options.searchparts, options.ignorecase, options.useregexp, options.invertmatch, options.accelchar)
        tofile = grepfilter.filterfile(self.xliff_parse(xliff_text))
        return str(tofile)

    def test_simplegrep(self):
        """grep for a simple string."""
        xliff_text = self.xliff_text
        xliff_file = self.xliff_parse(xliff_text)
        xliff_result = self.xliff_parse(self.xliff_grep(xliff_text, "rêd"))
        assert first_translatable(xliff_result).getsource() == u"rêd"
        assert first_translatable(xliff_result).gettarget() == u"rooi"

        xliff_result = self.xliff_parse(self.xliff_grep(xliff_text, "unavailable string"))
        assert xliff_result.isempty()


