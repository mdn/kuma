#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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

from pytest import mark

from translate.misc import wStringIO
from translate.storage import dtd, test_monolingual


def test_roundtrip_quoting():
    specials = [
        'Fish & chips',
        'five < six',
        'six > five',
        'Use &nbsp;',
        'Use &amp;nbsp;A "solution"',
        "skop 'n bal",
        '"""',
        "'''",
        '\n',
        '\t',
        '\r',
        'Escape at end \\',
        '',
        '\\n',
        '\\t',
        '\\r',
        '\\"',
        '\r\n',
        '\\r\\n',
        '\\',
        "Completed %S",
        "&blockAttackSites;",
        "&#x00A0;",
        "&intro-point2-a;",
        "&basePBMenu.label;",
        #"Don't buy",
        #"Don't \"buy\"",
        "A \"thing\"",
        "<a href=\"http"
    ]
    for special in specials:
        quoted_special = dtd.quotefordtd(special)
        unquoted_special = dtd.unquotefromdtd(quoted_special)
        print("special: %r\nquoted: %r\nunquoted: %r\n" % (special,
                                                           quoted_special,
                                                           unquoted_special))
        assert special == unquoted_special


@mark.xfail(reason="Not Implemented")
def test_quotefordtd_unimplemented_cases():
    """Test unimplemented quoting DTD cases."""
    assert dtd.quotefordtd("Between <p> and </p>") == ('"Between &lt;p&gt; and'
                                                       ' &lt;/p&gt;"')


def test_quotefordtd():
    """Test quoting DTD definitions"""
    assert dtd.quotefordtd('') == '""'
    assert dtd.quotefordtd("") == '""'
    assert dtd.quotefordtd("Completed %S") == '"Completed &#037;S"'
    assert dtd.quotefordtd("&blockAttackSites;") == '"&blockAttackSites;"'
    assert dtd.quotefordtd("&#x00A0;") == '"&#x00A0;"'
    assert dtd.quotefordtd("&intro-point2-a;") == '"&intro-point2-a;"'
    assert dtd.quotefordtd("&basePBMenu.label;") == '"&basePBMenu.label;"'
    # The ' character isn't escaped as &apos; since the " char isn't present.
    assert dtd.quotefordtd("Don't buy") == '"Don\'t buy"'
    # The ' character is escaped as &apos; because the " character is present.
    assert dtd.quotefordtd("Don't \"buy\"") == '"Don&apos;t &quot;buy&quot;"'
    assert dtd.quotefordtd("A \"thing\"") == '"A &quot;thing&quot;"'
    # The " character is not escaped when it indicates an attribute value.
    assert dtd.quotefordtd("<a href=\"http") == "'<a href=\"http'"
    # &amp;
    assert dtd.quotefordtd("Color & Light") == '"Color &amp; Light"'
    assert dtd.quotefordtd("Color & &block;") == '"Color &amp; &block;"'
    assert dtd.quotefordtd("Color&Light &red;") == '"Color&amp;Light &red;"'
    assert dtd.quotefordtd("Color & Light; Yes") == '"Color &amp; Light; Yes"'


@mark.xfail(reason="Not Implemented")
def test_unquotefromdtd_unimplemented_cases():
    """Test unimplemented unquoting DTD cases."""
    assert dtd.unquotefromdtd('"&lt;p&gt; and &lt;/p&gt;"') == "<p> and </p>"


def test_unquotefromdtd():
    """Test unquoting DTD definitions"""
    # %
    assert dtd.unquotefromdtd('"Completed &#037;S"') == "Completed %S"
    assert dtd.unquotefromdtd('"Completed &#37;S"') == "Completed %S"
    assert dtd.unquotefromdtd('"Completed &#x25;S"') == "Completed %S"
    # &entity;
    assert dtd.unquotefromdtd('"Color&light &block;"') == "Color&light &block;"
    assert dtd.unquotefromdtd('"Color & Light; Red"') == "Color & Light; Red"
    assert dtd.unquotefromdtd('"&blockAttackSites;"') == "&blockAttackSites;"
    assert dtd.unquotefromdtd('"&intro-point2-a;"') == "&intro-point2-a;"
    assert dtd.unquotefromdtd('"&basePBMenu.label"') == "&basePBMenu.label"
    # &amp;
    assert dtd.unquotefromdtd('"Color &amp; Light"') == "Color & Light"
    assert dtd.unquotefromdtd('"Color &amp; &block;"') == "Color & &block;"
    # nbsp
    assert dtd.unquotefromdtd('"&#x00A0;"') == "&#x00A0;"
    # '
    assert dtd.unquotefromdtd("'Don&apos;t buy'") == "Don't buy"
    # "
    assert dtd.unquotefromdtd("'Don&apos;t &quot;buy&quot;'") == 'Don\'t "buy"'
    assert dtd.unquotefromdtd('"A &quot;thing&quot;"') == "A \"thing\""
    assert dtd.unquotefromdtd('"A &#x0022;thing&#x0022;"') == "A \"thing\""
    assert dtd.unquotefromdtd("'<a href=\"http'") == "<a href=\"http"
    # other chars
    assert dtd.unquotefromdtd('"&#187;"') == u"»"


def test_android_roundtrip_quoting():
    specials = [
        "don't",
        'the "thing"'
    ]
    for special in specials:
        quoted_special = dtd.quoteforandroid(special)
        unquoted_special = dtd.unquotefromandroid(quoted_special)
        print("special: %r\nquoted: %r\nunquoted: %r\n" % (special,
                                                           quoted_special,
                                                           unquoted_special))
        assert special == unquoted_special


def test_quoteforandroid():
    """Test quoting Android DTD definitions."""
    assert dtd.quoteforandroid("don't") == r'"don\u0027t"'
    assert dtd.quoteforandroid('the "thing"') == r'"the \&quot;thing\&quot;"'


def test_unquotefromandroid():
    """Test unquoting Android DTD definitions."""
    assert dtd.unquotefromandroid('"Don\\&apos;t show"') == "Don't show"
    assert dtd.unquotefromandroid('"Don\\\'t show"') == "Don't show"
    assert dtd.unquotefromandroid('"Don\\u0027t show"') == "Don't show"
    assert dtd.unquotefromandroid('"A \\&quot;thing\\&quot;"') == "A \"thing\""


def test_removeinvalidamp(recwarn):
    """tests the the removeinvalidamps function"""

    def tester(actual, expected=None):
        if expected is None:
            expected = actual
        assert dtd.removeinvalidamps("test.name", actual) == expected
    # No errors
    tester("Valid &entity; included")
    tester("Valid &entity.name; included")
    tester("Valid &#1234; included")
    tester("Valid &entity_name;")
    # Errors that require & removal
    tester("This &amp is broken", "This amp is broken")
    tester("Mad & &amp &amp;", "Mad  amp &amp;")
    dtd.removeinvalidamps("simple.warningtest", "Dimpled &Ring")
    assert recwarn.pop(UserWarning)


class TestDTDUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = dtd.dtdunit

    def test_rich_get(self):
        pass

    def test_rich_set(self):
        pass


class TestDTD(test_monolingual.TestMonolingualStore):
    StoreClass = dtd.dtdfile

    def dtdparse(self, dtdsource):
        """helper that parses dtd source without requiring files"""
        dummyfile = wStringIO.StringIO(dtdsource)
        dtdfile = dtd.dtdfile(dummyfile)
        return dtdfile

    def dtdregen(self, dtdsource):
        """helper that converts dtd source to dtdfile object and back"""
        return str(self.dtdparse(dtdsource))

    def test_simpleentity(self):
        """checks that a simple dtd entity definition is parsed correctly"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        dtdunit = dtdfile.units[0]
        assert dtdunit.entity == "test.me"
        assert dtdunit.definition == '"bananas for sale"'

    def test_blanklines(self):
        """checks that blank lines don't break the parsing or regeneration"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_simpleentity_source(self):
        """checks that a simple dtd entity definition can be regenerated as source"""
        dtdsource = '<!ENTITY test.me "">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_hashcomment_source(self):
        """checks that a #expand comment is retained in the source"""
        dtdsource = '#expand <!ENTITY lang.version "__MOZILLA_LOCALE_VERSION__">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_commentclosing(self):
        """tests that comment closes with trailing space aren't duplicated"""
        dtdsource = '<!-- little comment --> \n<!ENTITY pane.title "Notifications">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_commententity(self):
        """check that we don't process messages in <!-- comments -->: bug 102"""
        dtdsource = '''<!-- commenting out until bug 38906 is fixed
<!ENTITY messagesHeader.label         "Messages"> -->'''
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        dtdunit = dtdfile.units[0]
        print(dtdunit)
        assert dtdunit.isnull()

    def test_newlines_in_entity(self):
        """tests that we can handle newlines in the entity itself"""
        dtdsource = '''<!ENTITY fileNotFound.longDesc "
<ul>
  <li>Check the file name for capitalisation or other typing errors.</li>
  <li>Check to see if the file was moved, renamed or deleted.</li>
</ul>
">
'''
        dtdregen = self.dtdregen(dtdsource)
        print(dtdregen)
        print(dtdsource)
        assert dtdsource == dtdregen

    def test_conflate_comments(self):
        """Tests that comments don't run onto the same line"""
        dtdsource = '<!-- test comments -->\n<!-- getting conflated -->\n<!ENTITY sample.txt "hello">\n'
        dtdregen = self.dtdregen(dtdsource)
        print(dtdsource)
        print(dtdregen)
        assert dtdsource == dtdregen

    def test_localisation_notes(self):
        """test to ensure that we retain the localisation note correctly"""
        dtdsource = '''<!--LOCALIZATION NOTE (publishFtp.label): Edit box appears beside this label -->
<!ENTITY publishFtp.label "If publishing to a FTP site, enter the HTTP address to browse to:">
'''
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_entitityreference_in_source(self):
        """checks that an &entity; in the source is retained"""
        dtdsource = '<!ENTITY % realBrandDTD SYSTEM "chrome://branding/locale/brand.dtd">\n%realBrandDTD;\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    #test for bug #610
    def test_entitityreference_order_in_source(self):
        """checks that an &entity; in the source is retained"""
        dtdsource = '<!ENTITY % realBrandDTD SYSTEM "chrome://branding/locale/brand.dtd">\n%realBrandDTD;\n<!-- some comment -->\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

        # The following test is identical to the one above, except that the entity is split over two lines.
        # This is to ensure that a recent bug fixed in dtdunit.parse() is at least partly documented.
        # The essence of the bug was that after it had read "realBrandDTD", the line index is not reset
        # before starting to parse the next line. It would then read the next available word (sequence of
        # alphanum characters) in stead of SYSTEM and then get very confused by not finding an opening ' or
        # " in the entity, borking the parsing for threst of the file.
        dtdsource = '<!ENTITY % realBrandDTD\n SYSTEM "chrome://branding/locale/brand.dtd">\n%realBrandDTD;\n'
        # FIXME: The following line is necessary, because of dtdfile's inability to remember the spacing of
        # the source DTD file when converting back to DTD.
        dtdregen = self.dtdregen(dtdsource).replace('realBrandDTD SYSTEM', 'realBrandDTD\n SYSTEM')
        print(dtdsource)
        print(dtdregen)
        assert dtdsource == dtdregen

    @mark.xfail(reason="Not Implemented")
    def test_comment_following(self):
        """check that comments that appear after and entity are not pushed onto another line"""
        dtdsource = '<!ENTITY textZoomEnlargeCmd.commandkey2 "="> <!-- + is above this key on many keyboards -->'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_comment_newline_space_closing(self):
        """check that comments that are closed by a newline then space then --> don't break the following entries"""
        dtdsource = '<!-- Comment\n -->\n<!ENTITY searchFocus.commandkey "k">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    @mark.xfail(reason="Not Implemented")
    def test_invalid_quoting(self):
        """checks that invalid quoting doesn't work - quotes can't be reopened"""
        # TODO: we should rather raise an error
        dtdsource = '<!ENTITY test.me "bananas for sale""room">\n'
        assert dtd.unquotefromdtd(dtdsource[dtdsource.find('"'):]) == 'bananas for sale'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        dtdunit = dtdfile.units[0]
        assert dtdunit.definition == '"bananas for sale"'
        assert str(dtdfile) == '<!ENTITY test.me "bananas for sale">\n'

    def test_missing_quotes(self, recwarn):
        """test that we fail graacefully when a message without quotes is found (bug #161)"""
        dtdsource = '<!ENTITY bad no quotes">\n<!ENTITY good "correct quotes">\n'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        assert recwarn.pop(Warning)

    # Test for bug #68
    def test_entity_escaping(self):
        """Test entities escaping (&amp; &quot; &lt; &gt; &apos;) (bug #68)"""
        dtdsource = ('<!ENTITY securityView.privacy.header "Privacy &amp; '
                     'History">\n<!ENTITY rights.safebrowsing-term3 "Uncheck '
                     'the options to &quot;&blockAttackSites.label;&quot; and '
                     '&quot;&blockWebForgeries.label;&quot;">\n<!ENTITY '
                     'translate.test1 \'XML encodings don&apos;t work\'>\n'
                     '<!ENTITY translate.test2 "In HTML the text paragraphs '
                     'are enclosed between &lt;p&gt; and &lt;/p&gt; tags.">\n')
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 4
        #dtdunit = dtdfile.units[0]
        #assert dtdunit.definition == '"Privacy &amp; History"'
        #assert dtdunit.target == "Privacy & History"
        #assert dtdunit.source == "Privacy & History"
        dtdunit = dtdfile.units[1]
        assert dtdunit.definition == ('"Uncheck the options to &quot;'
                                      '&blockAttackSites.label;&quot; and '
                                      '&quot;&blockWebForgeries.label;&quot;"')
        assert dtdunit.target == ("Uncheck the options to \""
                                  "&blockAttackSites.label;\" and \""
                                  "&blockWebForgeries.label;\"")
        assert dtdunit.source == ("Uncheck the options to \""
                                  "&blockAttackSites.label;\" and \""
                                  "&blockWebForgeries.label;\"")
        dtdunit = dtdfile.units[2]
        assert dtdunit.definition == "'XML encodings don&apos;t work'"
        assert dtdunit.target == "XML encodings don\'t work"
        assert dtdunit.source == "XML encodings don\'t work"
        #dtdunit = dtdfile.units[3]
        #assert dtdunit.definition == ('"In HTML the text paragraphs are '
        #                              'enclosed between &lt;p&gt; and &lt;/p'
        #                              '&gt; tags."')
        #assert dtdunit.target == ("In HTML the text paragraphs are enclosed "
        #                          "between <p> and </p> tags.")
        #assert dtdunit.source == ("In HTML the text paragraphs are enclosed "
        #                          "between <p> and </p> tags.")

    # Test for bug #68
    def test_entity_escaping_roundtrip(self):
        """Test entities escaping roundtrip (&amp; &quot; ...) (bug #68)"""
        dtdsource = ('<!ENTITY securityView.privacy.header "Privacy &amp; '
                     'History">\n<!ENTITY rights.safebrowsing-term3 "Uncheck '
                     'the options to &quot;&blockAttackSites.label;&quot; and '
                     '&quot;&blockWebForgeries.label;&quot;">\n<!ENTITY '
                     'translate.test1 \'XML encodings don&apos;t work\'>\n'
                     '<!ENTITY translate.test2 "In HTML the text paragraphs '
                     'are enclosed between &lt;p&gt; and &lt;/p&gt; tags.">\n')
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen


class TestAndroidDTD(test_monolingual.TestMonolingualStore):
    StoreClass = dtd.dtdfile

    def dtdparse(self, dtdsource):
        """Parses an Android DTD source string and returns a DTD store.

        This allows to simulate reading from Android DTD files without really
        having real Android DTD files.
        """
        dummyfile = wStringIO.StringIO(dtdsource)
        dtdfile = dtd.dtdfile(dummyfile, android=True)
        return dtdfile

    def dtdregen(self, dtdsource):
        """Parses an Android DTD string to DTD store and then converts it back.

        This allows to simulate reading from an Android DTD file to an
        in-memory store and writing back to an Android DTD file without really
        having a real file.
        """
        return str(self.dtdparse(dtdsource))

    # Test for bug #2480
    def test_android_single_quote_escape(self):
        """Checks several single quote unescaping cases in Android DTD.

        See bug #2480.
        """
        dtdsource = ('<!ENTITY pref_char_encoding_off "Don\\\'t show menu">\n'
                     '<!ENTITY sync.nodevice.label \'Don\\&apos;t show\'>\n'
                     '<!ENTITY sync.nodevice.label "Don\\u0027t show">\n')
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 3
        dtdunit = dtdfile.units[0]
        assert dtdunit.definition == '"Don\\\'t show menu"'
        assert dtdunit.target == "Don't show menu"
        assert dtdunit.source == "Don't show menu"
        dtdunit = dtdfile.units[1]
        assert dtdunit.definition == "'Don\\&apos;t show'"
        assert dtdunit.target == "Don't show"
        assert dtdunit.source == "Don't show"
        dtdunit = dtdfile.units[2]
        assert dtdunit.definition == '"Don\\u0027t show"'
        assert dtdunit.target == "Don't show"
        assert dtdunit.source == "Don't show"

    # Test for bug #2480
    def test_android_single_quote_escape_parse_and_convert_back(self):
        """Checks that Android DTD don't change after parse and convert back.

        An Android DTD source string with several single quote escapes is used
        instead of real files.

        See bug #2480.
        """
        dtdsource = ('<!ENTITY pref_char_encoding_off "Don\\\'t show menu">\n'
                     '<!ENTITY sync.nodevice.label \'Don\\&apos;t show\'>\n'
                     '<!ENTITY sync.nodevice.label "Don\\u0027t show">\n')
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_android_double_quote_escape(self):
        """Checks double quote unescaping in Android DTD."""
        dtdsource = '<!ENTITY translate.test "A \\&quot;thing\\&quot;">\n'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        dtdunit = dtdfile.units[0]
        assert dtdunit.definition == '"A \\&quot;thing\\&quot;"'
        assert dtdunit.target == "A \"thing\""
        assert dtdunit.source == "A \"thing\""

    def test_android_double_quote_escape_parse_and_convert_back(self):
        """Checks that Android DTD don't change after parse and convert back.

        An Android DTD source string with double quote escapes is used instead
        of real files.
        """
        dtdsource = '<!ENTITY translate.test "A \\&quot;thing\\&quot;">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen
