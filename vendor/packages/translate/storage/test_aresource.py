#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree

from translate.storage import aresource, test_monolingual
from translate.misc.multistring import multistring
from translate.storage.base import TranslationStore


class TestAndroidResourceUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = aresource.AndroidResourceUnit

    def __check_escape(self, string, xml, target_language=None):
        """Helper that checks that a string is output with the right escape."""
        unit = self.UnitClass("Test String")

        if (target_language is not None):
            store = TranslationStore()
            store.settargetlanguage(target_language)
            unit._store = store

        unit.target = string

        print("unit.target:", repr(unit.target))
        print("xml:", repr(xml))

        assert str(unit) == xml

    def __check_parse(self, string, xml):
        """Helper that checks that a string is parsed correctly."""
        parser = etree.XMLParser(strip_cdata=False)

        translatable = 'translatable="false"' not in xml
        et = etree.fromstring(xml, parser)
        unit = self.UnitClass.createfromxmlElement(et)

        print("unit.target:", repr(unit.target))
        print("string:", string)
        print("translatable:", repr(unit.istranslatable()))

        assert unit.target == string
        assert unit.istranslatable() == translatable

    ############################ Check string escape ##########################

    def test_escape_message_with_newline(self):
        string = 'message\nwith newline'
        xml = '<string name="Test String">message\\nwith newline</string>\n\n'
        self.__check_escape(string, xml)

    def test_escape_message_with_newline_in_xml(self):
        string = 'message \nwith newline in xml'
        xml = ('<string name="Test String">message\n\\nwith newline in xml'
               '</string>\n\n')
        self.__check_escape(string, xml)

    def test_escape_twitter(self):
        string = '@twitterescape'
        xml = '<string name="Test String">\\@twitterescape</string>\n\n'
        self.__check_escape(string, xml)

    def test_escape_quote(self):
        string = 'quote \'escape\''
        xml = '<string name="Test String">quote \\\'escape\\\'</string>\n\n'
        self.__check_escape(string, xml)

    def test_escape_double_space(self):
        string = 'double  space'
        xml = '<string name="Test String">"double  space"</string>\n\n'
        self.__check_escape(string, xml)

    def test_escape_leading_space(self):
        string = ' leading space'
        xml = '<string name="Test String">" leading space"</string>\n\n'
        self.__check_escape(string, xml)

    def test_escape_xml_entities(self):
        string = '>xml&entities'
        xml = '<string name="Test String">&gt;xml&amp;entities</string>\n\n'
        self.__check_escape(string, xml)

    def test_escape_html_code(self):
        string = 'some <b>html code</b> here'
        xml = ('<string name="Test String">some <b>html code</b> here'
               '</string>\n\n')
        self.__check_escape(string, xml)

    def test_escape_html_code_quote(self):
        string = 'some <b>html code</b> \'here\''
        xml = ('<string name="Test String">some <b>html code</b> \\\'here\\\''
               '</string>\n\n')
        self.__check_escape(string, xml)

    def test_escape_arrows(self):
        string = '<<< arrow'
        xml = '<string name="Test String">&lt;&lt;&lt; arrow</string>\n\n'
        self.__check_escape(string, xml)

    def test_escape_link(self):
        string = '<a href="http://example.net">link</a>'
        xml = ('<string name="Test String"><a href="http://example.net">link'
               '</a></string>\n\n')
        self.__check_escape(string, xml)

    def test_escape_link_and_text(self):
        string = '<a href="http://example.net">link</a> and text'
        xml = ('<string name="Test String"><a href="http://example.net">link'
               '</a> and text</string>\n\n')
        self.__check_escape(string, xml)

    def test_escape_blank_string(self):
        string = ''
        xml = '<string name="Test String"></string>\n\n'
        self.__check_escape(string, xml)

    def test_plural_escape_message_with_newline(self):
        mString = multistring(['one message\nwith newline', 'other message\nwith newline'])
        xml = ('<plurals name="Test String">\n\t'
                 '<item quantity="one">one message\\nwith newline</item>\n\t'
                 '<item quantity="other">other message\\nwith newline</item>\n'
               '</plurals>\n')
        self.__check_escape(mString, xml, 'en')

    ############################ Check string parse ###########################

    def test_parse_message_with_newline(self):
        string = 'message\nwith newline'
        xml = '<string name="Test String">message\\nwith newline</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_message_with_newline_in_xml(self):
        string = 'message \nwith newline in xml'
        xml = ('<string name="Test String">message\n\\nwith newline in xml'
               '</string>\n\n')
        self.__check_parse(string, xml)

    def test_parse_twitter(self):
        string = '@twitterescape'
        xml = '<string name="Test String">\\@twitterescape</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_quote(self):
        string = 'quote \'escape\''
        xml = '<string name="Test String">quote \\\'escape\\\'</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_double_space(self):
        string = 'double  space'
        xml = '<string name="Test String">"double  space"</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_leading_space(self):
        string = ' leading space'
        xml = '<string name="Test String">" leading space"</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_xml_entities(self):
        string = '>xml&entities'
        xml = '<string name="Test String">&gt;xml&amp;entities</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_html_code(self):
        string = 'some <b>html code</b> here'
        xml = ('<string name="Test String">some <b>html code</b> here'
               '</string>\n\n')
        self.__check_parse(string, xml)

    def test_parse_arrows(self):
        string = '<<< arrow'
        xml = '<string name="Test String">&lt;&lt;&lt; arrow</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_link(self):
        string = '<a href="http://example.net">link</a>'
        xml = ('<string name="Test String"><a href="http://example.net">link'
               '</a></string>\n\n')
        self.__check_parse(string, xml)

    def test_parse_link_and_text(self):
        string = '<a href="http://example.net">link</a> and text'
        xml = ('<string name="Test String"><a href="http://example.net">link'
               '</a> and text</string>\n\n')
        self.__check_parse(string, xml)

    def test_parse_blank_string(self):
        string = ''
        xml = '<string name="Test String"></string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_blank_string_again(self):
        string = ''
        xml = '<string name="Test String"/>\n\n'
        self.__check_parse(string, xml)

    def test_parse_double_quotes_string(self):
        """Check that double quotes got removed."""
        string = 'double quoted text'
        xml = '<string name="Test String">"double quoted text"</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_newline_in_string(self):
        """Check that newline is read as space.

        At least it seems to be what Android does.
        """
        string = 'newline in string'
        xml = '<string name="Test String">newline\nin string</string>\n\n'
        self.__check_parse(string, xml)

    def test_parse_not_translatable_string(self):
        string = 'string'
        xml = ('<string name="Test String" translatable="false">string'
               '</string>\n\n')
        self.__check_parse(string, xml)

    def test_plural_parse_message_with_newline(self):
        mString = multistring(['one message\nwith newline', 'other message\nwith newline'])
        xml = ('<plurals name="Test String">\n\t'
                 '<item quantity="one">one message\\nwith newline</item>\n\t'
                 '<item quantity="other">other message\\nwith newline</item>\n'
               '</plurals>\n')
        self.__check_parse(mString, xml)


class TestAndroidResourceFile(test_monolingual.TestMonolingualStore):
    StoreClass = aresource.AndroidResourceFile

    def test_targetlanguage_default_handlings(self):
        store = self.StoreClass()

        # Initial value is None
        assert store.gettargetlanguage() is None

        # sourcelanguage shouldn't change the targetlanguage
        store.setsourcelanguage('en')
        assert store.gettargetlanguage() is None

        # targetlanguage setter works correctly
        store.settargetlanguage('de')
        assert store.gettargetlanguage() == 'de'

        # explicit targetlanguage wins over filename
        store.filename = 'dommy/values-it/res.xml'
        assert store.gettargetlanguage() == 'de'

    def test_targetlanguage_auto_detection_filename(self):
        store = self.StoreClass()

        # Check language auto_detection
        store.filename = 'project/values-it/res.xml'
        assert store.gettargetlanguage() == 'it'

    def test_targetlanguage_auto_detection_filename_default_language(self):
        store = self.StoreClass()

        store.setsourcelanguage('en')

        # Check language auto_detection
        store.filename = 'project/values/res.xml'
        assert store.gettargetlanguage() == 'en'

    def test_targetlanguage_auto_detection_invalid_filename(self):
        store = self.StoreClass()

        store.setsourcelanguage('en')

        store.filename = 'project/invalid_directory/res.xml'
        assert store.gettargetlanguage() is None

        store.filename = 'invalid_directory'
        assert store.gettargetlanguage() is None
