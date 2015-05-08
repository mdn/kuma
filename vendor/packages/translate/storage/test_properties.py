#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import deprecated_call, raises

from translate.misc import wStringIO
from translate.storage import properties, test_monolingual


def test_find_delimiter_pos_simple():
    """Simple tests to find the various delimiters"""
    assert properties._find_delimiter(u"key=value", [u"=", u":", u" "]) == ('=', 3)
    assert properties._find_delimiter(u"key:value", [u"=", u":", u" "]) == (':', 3)
    assert properties._find_delimiter(u"key value", [u"=", u":", u" "]) == (' ', 3)
    # NOTE this is valid in Java properties, the key is then the empty string
    assert properties._find_delimiter(u"= value", [u"=", u":", u" "]) == ('=', 0)


def test_find_delimiter_pos_multiple():
    """Find delimiters when multiple potential delimiters are involved"""
    assert properties._find_delimiter(u"key=value:value", [u"=", u":", u" "]) == ('=', 3)
    assert properties._find_delimiter(u"key:value=value", [u"=", u":", u" "]) == (':', 3)
    assert properties._find_delimiter(u"key value=value", [u"=", u":", u" "]) == (' ', 3)


def test_find_delimiter_pos_none():
    """Find delimiters when there isn't one"""
    assert properties._find_delimiter(u"key", [u"=", u":", u" "]) == (None, -1)
    assert properties._find_delimiter(u"key\=\:\ ", [u"=", u":", u" "]) == (None, -1)


def test_find_delimiter_pos_whitespace():
    """Find delimiters when whitespace is involved"""
    assert properties._find_delimiter(u"key = value", [u"=", u":", u" "]) == ('=', 4)
    assert properties._find_delimiter(u"key : value", [u"=", u":", u" "]) == (':', 4)
    assert properties._find_delimiter(u"key   value", [u"=", u":", u" "]) == (' ', 3)
    assert properties._find_delimiter(u"key value = value", [u"=", u":", u" "]) == (' ', 3)
    assert properties._find_delimiter(u"key value value", [u"=", u":", u" "]) == (' ', 3)
    assert properties._find_delimiter(u" key = value", [u"=", u":", u" "]) == ('=', 5)


def test_find_delimiter_pos_escapes():
    """Find delimiters when potential earlier delimiters are escaped"""
    assert properties._find_delimiter(u"key\:=value", [u"=", u":", u" "]) == ('=', 5)
    assert properties._find_delimiter(u"key\=: value", [u"=", u":", u" "]) == (':', 5)
    assert properties._find_delimiter(u"key\   value", [u"=", u":", u" "]) == (' ', 5)
    assert properties._find_delimiter(u"key\ key\ key\: = value", [u"=", u":", u" "]) == ('=', 16)


def test_find_delimiter_deprecated_fn():
    """Test that the deprecated function still actually works"""
    assert properties.find_delimeter(u"key=value") == ('=', 3)
    deprecated_call(properties.find_delimeter, u"key=value")


def test_is_line_continuation():
    assert not properties.is_line_continuation(u"")
    assert not properties.is_line_continuation(u"some text")
    assert properties.is_line_continuation(u"""some text\\""")
    assert not properties.is_line_continuation(u"""some text\\\\""")  # Escaped \
    assert properties.is_line_continuation(u"""some text\\\\\\""")  # Odd num. \ is line continuation
    assert properties.is_line_continuation(u"""\\\\\\""")


def test_key_strip():
    assert properties._key_strip(u"key") == "key"
    assert properties._key_strip(u" key") == "key"
    assert properties._key_strip(u"\ key") == "\ key"
    assert properties._key_strip(u"key ") == "key"
    assert properties._key_strip(u"key\ ") == "key\ "


def test_is_comment_one_line():
    assert properties.is_comment_one_line("# comment")
    assert properties.is_comment_one_line("! comment")
    assert properties.is_comment_one_line("// comment")
    assert properties.is_comment_one_line("  # comment")
    assert properties.is_comment_one_line("/* comment */")
    assert not properties.is_comment_one_line("not = comment_line /* comment */")
    assert not properties.is_comment_one_line("/* comment ")


def test_is_comment_start():
    assert properties.is_comment_start("/* comment")
    assert not properties.is_comment_start("/* comment */")


def test_is_comment_end():
    assert properties.is_comment_end(" comment */")
    assert not properties.is_comment_end("/* comment */")


class TestPropUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = properties.propunit

    def test_rich_get(self):
        pass

    def test_rich_set(self):
        pass


class TestProp(test_monolingual.TestMonolingualStore):
    StoreClass = properties.propfile

    def propparse(self, propsource, personality="java", encoding=None):
        """helper that parses properties source without requiring files"""
        dummyfile = wStringIO.StringIO(propsource)
        propfile = properties.propfile(dummyfile, personality, encoding)
        return propfile

    def propregen(self, propsource):
        """helper that converts properties source to propfile object and back"""
        return str(self.propparse(propsource))

    def test_simpledefinition(self):
        """checks that a simple properties definition is parsed correctly"""
        propsource = 'test_me=I can code!'
        propfile = self.propparse(propsource)
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == "test_me"
        assert propunit.source == "I can code!"

    def test_simpledefinition_source(self):
        """checks that a simple properties definition can be regenerated as source"""
        propsource = 'test_me=I can code!'
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_unicode_escaping(self):
        """check that escaped unicode is converted properly"""
        propsource = "unicode=\u0411\u0416\u0419\u0428"
        messagevalue = u'\u0411\u0416\u0419\u0428'.encode("UTF-8")
        propfile = self.propparse(propsource, personality="mozilla")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == "unicode"
        assert propunit.source.encode("UTF-8") == "БЖЙШ"
        regensource = str(propfile)
        assert messagevalue in regensource
        assert "\\u" not in regensource

    def test_newlines_startend(self):
        """check that we preserve \n that appear at start and end of properties"""
        propsource = "newlines=\\ntext\\n"
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_whitespace_handling(self):
        """check that we remove extra whitespace around property"""
        whitespaces = (
            ('key = value', 'key', 'value'),      # Standard for baseline
            (' key =  value', 'key', 'value'),    # Extra \s before key and value
            ('\ key\ = value', '\ key\ ', 'value'),  # extra space at start and end of key
            ('key = \ value ', 'key', ' value '),  # extra space at start end end of value
        )
        for propsource, key, value in whitespaces:
            propfile = self.propparse(propsource)
            propunit = propfile.units[0]
            print(repr(propsource), repr(propunit.name), repr(propunit.source))
            assert propunit.name == key
            assert propunit.source == value
            # let's reparse the output to ensure good serialisation->parsing roundtrip:
            propfile = self.propparse(str(propunit))
            propunit = propfile.units[0]
            assert propunit.name == key
            assert propunit.source == value

    def test_key_value_delimiters_simple(self):
        """test that we can handle colon, equals and space delimiter
        between key and value.  We don't test any space removal or escaping"""
        delimiters = [":", "=", " "]
        for delimiter in delimiters:
            propsource = "key%svalue" % delimiter
            print("source: '%s'\ndelimiter: '%s'" % (propsource, delimiter))
            propfile = self.propparse(propsource)
            assert len(propfile.units) == 1
            propunit = propfile.units[0]
            assert propunit.name == "key"
            assert propunit.source == "value"

    def test_comments(self):
        """checks that we handle # and ! comments"""
        markers = ['#', '!']
        for comment_marker in markers:
            propsource = '''%s A comment
key=value
''' % comment_marker
            propfile = self.propparse(propsource)
            print(repr(propsource))
            print("Comment marker: '%s'" % comment_marker)
            assert len(propfile.units) == 1
            propunit = propfile.units[0]
            assert propunit.comments == ['%s A comment' % comment_marker]

    def test_latin1(self):
        """checks that we handle non-escaped latin1 text"""
        prop_source = u"key=valú".encode('latin1')
        prop_store = self.propparse(prop_source)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        assert unit.source == u"valú"

    def test_fullspec_delimiters(self):
        """test the full definiation as found in Java docs"""
        proplist = ['Truth = Beauty\n', '       Truth:Beauty', 'Truth                  :Beauty', 'Truth        Beauty']
        for propsource in proplist:
            propfile = self.propparse(propsource)
            propunit = propfile.units[0]
            print(propunit)
            assert propunit.name == "Truth"
            assert propunit.source == "Beauty"

    def test_fullspec_escaped_key(self):
        """Escaped delimeters can be in the key"""
        prop_source = u"\:\="
        prop_store = self.propparse(prop_source)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        print(unit)
        assert unit.name == u"\:\="

    def test_fullspec_line_continuation(self):
        """Whitespace delimiter and pre whitespace in line continuation are dropped"""
        prop_source = ur"""fruits                           apple, banana, pear, \
                                  cantaloupe, watermelon, \
                                  kiwi, mango
"""
        prop_store = self.propparse(prop_source)
        print(prop_store)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        print(unit)
        assert properties._find_delimiter(prop_source, [u"=", u":", u" "]) == (' ', 6)
        assert unit.name == u"fruits"
        assert unit.source == u"apple, banana, pear, cantaloupe, watermelon, kiwi, mango"

    def test_fullspec_key_without_value(self):
        """A key can have no value in which case the value is the empty string"""
        prop_source = u"cheeses"
        prop_store = self.propparse(prop_source)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        print(unit)
        assert unit.name == u"cheeses"
        assert unit.source == u""

    def test_mac_strings(self):
        """test various items used in Mac OS X strings files"""
        propsource = ur'''"I am a \"key\"" = "I am a \"value\"";'''.encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == ur'I am a "key"'
        assert propunit.source.encode('utf-8') == u'I am a "value"'

    def test_mac_strings_unicode(self):
        """Ensure we can handle Unicode"""
        propsource = ur'''"I am a “key”" = "I am a “value”";'''.encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == ur'I am a “key”'
        assert propfile.personality.encode(propunit.source) == u'I am a “value”'

    def test_mac_strings_utf8(self):
        """Ensure we can handle Unicode"""
        propsource = ur'''"I am a “key”" = "I am a “value”";'''.encode('utf-8')
        propfile = self.propparse(propsource, personality="strings-utf8")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == ur'I am a “key”'
        assert propfile.personality.encode(propunit.source) == u'I am a “value”'

    def test_mac_strings_newlines(self):
        """test newlines \n within a strings files"""
        propsource = ur'''"key" = "value\nvalue";'''.encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == u'key'
        assert propunit.source.encode('utf-8') == u'value\nvalue'
        assert propfile.personality.encode(propunit.source) == ur'value\nvalue'

    def test_mac_strings_comments(self):
        """test .string comment types"""
        propsource = ur'''/* Comment */
// Comment
"key" = "value";'''.encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == u'key'
        assert propunit.source.encode('utf-8') == u'value'
        assert propunit.getnotes() == u"/* Comment */\n// Comment"

    def test_mac_strings_multilines_comments(self):
        """test .string multiline comments"""
        propsource = (u'/* Foo\n'
                      u'Bar\n'
                      u'Baz */\n'
                      u'"key" = "value"').encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == u'key'
        assert propunit.source.encode('utf-8') == u'value'
        assert propunit.getnotes() == u"/* Foo\nBar\nBaz */"

    def test_mac_strings_comments_dropping(self):
        """.string generic (and unuseful) comments should be dropped"""
        propsource = ur'''/* No comment provided by engineer. */
"key" = "value";'''.encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == u'key'
        assert propunit.source.encode('utf-8') == u'value'
        assert propunit.getnotes() == u""

    def test_mac_strings_quotes(self):
        """test that parser unescapes characters used as wrappers"""
        propsource = ur'"key with \"quotes\"" = "value with \"quotes\"";'.encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        propunit = propfile.units[0]
        assert propunit.name == ur'key with "quotes"'
        assert propunit.value == ur'value with "quotes"'

    def test_mac_strings_serialization(self):
        """test that serializer quotes mac strings properly"""
        propsource = ur'"key with \"quotes\"" = "value with \"quotes\"";'.encode('utf-16')
        propfile = self.propparse(propsource, personality="strings")
        # we don't care about leading and trailing newlines and zero bytes
        # in the assert, we just want to make sure that
        # - all quotes are in place
        # - quotes inside are escaped
        # - for the sake of beauty a pair of spaces encloses the equal mark
        # - every line ends with ";"
        assert str(propfile.units[0]).strip('\n\x00') == propsource.strip('\n\x00')
        assert str(propfile).strip('\n\x00') == propsource.strip('\n\x00')

    def test_override_encoding(self):
        """test that we can override the encoding of a properties file"""
        propsource = u"key = value".encode("cp1252")
        propfile = self.propparse(propsource, personality="strings", encoding="cp1252")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == u'key'
        assert propunit.source == u'value'

    def test_trailing_comments(self):
        """test that we handle non-unit data at the end of a file"""
        propsource = u"key = value\n# END"
        propfile = self.propparse(propsource)
        assert len(propfile.units) == 2
        propunit = propfile.units[1]
        assert propunit.name == u''
        assert propunit.source == u''
        assert propunit.getnotes() == u"# END"

    def test_utf16_byte_order_mark(self):
        """test that BOM appears in the resulting text once only"""
        propsource = u"key1 = value1\nkey2 = value2\n".encode('utf-16')
        propfile = self.propparse(propsource, encoding='utf-16')
        result = str(propfile)
        bom = propsource[:2]
        assert result.startswith(bom)
        assert bom not in result[2:]

    def test_raise_ioerror_if_cannot_detect_encoding(self):
        """Test that IOError is thrown if file encoding cannot be detected."""
        propsource = u"key = ąćęłńóśźż".encode("cp1250")
        with raises(IOError):
            self.propparse(propsource, personality="strings")
