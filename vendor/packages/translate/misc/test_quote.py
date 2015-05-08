#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.misc import quote


def test_find_all():
    """tests the find_all function"""
    assert quote.find_all("", "a") == []
    assert quote.find_all("a", "b") == []
    assert quote.find_all("a", "a") == [0]
    assert quote.find_all("aa", "a") == [0, 1]
    assert quote.find_all("abba", "ba") == [2]
    # check we skip the whole instance
    assert quote.find_all("banana", "ana") == [1]


def test_extract():
    """tests the extract function"""
    assert quote.extract("the <quoted> part", "<", ">", "\\", 0) == ("<quoted>", False)
    assert quote.extract("the 'quoted' part", "'", "'", "\\", 0) == ("'quoted'", False)
    assert quote.extract("the 'isn\\'t escaping fun' part", "'", "'", "\\", 0) == ("'isn\\'t escaping fun'", False)
    assert quote.extract("the 'isn\\'t something ", "'", "'", "\\", 0) == ("'isn\\'t something ", True)
    assert quote.extract("<quoted>\\", "<", ">", "\\", 0) == ("<quoted>", False)
    assert quote.extract("<quoted><again>", "<", ">", "\\", 0) == ("<quoted><again>", False)
    assert quote.extract("<quoted>\\\\<again>", "<", ">", "\\", 0) == ("<quoted><again>", False)
    assert quote.extract("<quoted\\>", "<", ">", "\\", 0) == ("<quoted\\>", True)
    assert quote.extract(' -->\n<!ENTITY blah "Some">', "<!--", "-->", None, 1) == (" -->", False)
    assert quote.extract('">\n', '"', '"', None, True) == ('"', False)


def test_extractwithoutquotes():
    """tests the extractwithoutquotes function"""
    assert quote.extractwithoutquotes("the <quoted> part", "<", ">", "\\", 0) == ("quoted", False)
    assert quote.extractwithoutquotes("the 'quoted' part", "'", "'", "\\", 0) == ("quoted", False)
    assert quote.extractwithoutquotes("the 'isn\\'t escaping fun' part", "'", "'", "\\", 0) == ("isn\\'t escaping fun", False)
    assert quote.extractwithoutquotes("the 'isn\\'t something ", "'", "'", "\\", 0) == ("isn\\'t something ", True)
    assert quote.extractwithoutquotes("<quoted>\\", "<", ">", "\\", 0) == ("quoted", False)
    assert quote.extractwithoutquotes("<quoted>\\\\<again>", "<", ">", "\\", 0) == ("quotedagain", False)
    assert quote.extractwithoutquotes("<quoted><again\\\\", "<", ">", "\\", 0, True) == ("quotedagain\\\\", True)
    # don't include escapes...
    assert quote.extractwithoutquotes("the 'isn\\'t escaping fun' part", "'", "'", "\\", 0, False) == ("isn't escaping fun", False)
    assert quote.extractwithoutquotes("the 'isn\\'t something ", "'", "'", "\\", 0, False) == ("isn't something ", True)
    assert quote.extractwithoutquotes("<quoted\\", "<", ">", "\\", 0, False) == ("quoted", True)
    assert quote.extractwithoutquotes("<quoted><again\\\\", "<", ">", "\\", 0, False) == ("quotedagain\\", True)
    # escaping of quote char
    assert quote.extractwithoutquotes("<quoted\\>", "<", ">", "\\", 0, False) == ("quoted>", True)


def isnewlineortabescape(escape):
    if escape == "\\n" or escape == "\\t":
        return escape
    return escape[-1]


def test_extractwithoutquotes_passfunc():
    """tests the extractwithoutquotes function with a function for includeescapes as a parameter"""
    assert quote.extractwithoutquotes("<test \\r \\n \\t \\\\>", "<", ">", "\\", 0, isnewlineortabescape) == ("test r \\n \\t \\", False)


def test_stripcomment():
    assert quote.stripcomment("<!-- Comment -->") == "Comment"


class TestEncoding:

    def test_javepropertiesencode(self):
        assert quote.javapropertiesencode(u"abc") == u"abc"
        assert quote.javapropertiesencode(u"abcḓ") == "abc\u1E13"
        assert quote.javapropertiesencode(u"abc\n") == u"abc\\n"

    def test_mozillapropertiesencode(self):
        assert quote.mozillapropertiesencode(u"abc") == u"abc"
        assert quote.mozillapropertiesencode(u"abcḓ") == u"abcḓ"
        assert quote.mozillapropertiesencode(u"abc\n") == u"abc\\n"

    def test_escapespace(self):
        assert quote.escapespace(u" ") == u"\\u0020"
        assert quote.escapespace(u"\t") == u"\\u0009"

    def test_mozillaescapemarginspaces(self):
        assert quote.mozillaescapemarginspaces(u" ") == u""
        assert quote.mozillaescapemarginspaces(u"A") == u"A"
        assert quote.mozillaescapemarginspaces(u" abc ") == u"\\u0020abc\\u0020"
        assert quote.mozillaescapemarginspaces(u"  abc ") == u"\\u0020 abc\\u0020"

    def test_mozilla_control_escapes(self):
        r"""test that we do \uNNNN escapes for certain control characters instead of converting to UTF-8 characters"""
        prefix, suffix = "bling", "blang"
        for control in (u"\u0005", u"\u0006", u"\u0007", u"\u0011"):
            string = prefix + control + suffix
            assert quote.escapecontrols(string) == string

    def test_propertiesdecode(self):
        assert quote.propertiesdecode(u"abc") == u"abc"
        assert quote.propertiesdecode(u"abc\u1e13") == u"abcḓ"
        assert quote.propertiesdecode(u"abc\u1E13") == u"abcḓ"
        assert quote.propertiesdecode(u"abc\N{LEFT CURLY BRACKET}") == u"abc{"
        assert quote.propertiesdecode(u"abc\\") == u"abc\\"
        assert quote.propertiesdecode(u"abc\\") == u"abc\\"

    def test_properties_decode_slashu(self):
        assert quote.propertiesdecode(u"abc\u1e13") == u"abcḓ"
        assert quote.propertiesdecode(u"abc\u0020") == u"abc "
        # NOTE Java only accepts 4 digit unicode, Mozilla accepts two
        # unfortunately, but it seems harmless to accept both.
        assert quote.propertiesdecode("abc\u20") == u"abc "

    def _html_encoding_helper(self, pairs):
        for from_, to in pairs:
            assert quote.htmlentityencode(from_) == to
            assert quote.htmlentitydecode(to) == from_

    def test_htmlencoding(self):
        """test that we can encode and decode simple HTML entities"""
        raw_encoded = [(u"€", u"&euro;"), (u"©", u"&copy;"), (u'"', u"&quot;")]
        self._html_encoding_helper(raw_encoded)

    def test_htmlencoding_existing_entities(self):
        """test that we don't mess existing entities"""
        assert quote.htmlentityencode(u"&amp;") == u"&amp;"

    def test_htmlencoding_passthrough(self):
        """test that we can encode and decode things that look like HTML entities but aren't"""
        raw_encoded = [(u"copy quot", u"copy quot"),]     # Raw text should have nothing done to it.
        self._html_encoding_helper(raw_encoded)

    def test_htmlencoding_nonentities(self):
        """tests to give us full coverage"""
        for encoded, real in [(u"Some &; text", u"Some &; text"),
                              (u"&copy ", u"&copy "),
                              (u"&copy", u"&copy"),
                              (u"&rogerrabbit;", u"&rogerrabbit;"),]:
            assert quote.htmlentitydecode(encoded) == real

        for decoded, real in [(u"Some &; text", u"Some &; text"),
                              (u"&copy ", u"&amp;copy "),
                              (u"&copy", u"&amp;copy"),
                              (u"&rogerrabbit;", u"&rogerrabbit;"),]:
            assert quote.htmlentityencode(decoded) == real
