# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2010 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

from datetime import datetime
import doctest
from StringIO import StringIO
import unittest

from babel.messages.catalog import Catalog, Message
from babel.messages import pofile
from babel.util import FixedOffsetTimezone, LOCALTZ


class ReadPoTestCase(unittest.TestCase):

    def test_preserve_locale(self):
        buf = StringIO(r'''msgid "foo"
msgstr "Voh"''')
        catalog = pofile.read_po(buf, locale='en_US')
        self.assertEqual('en_US', catalog.locale)

    def test_preserve_domain(self):
        buf = StringIO(r'''msgid "foo"
msgstr "Voh"''')
        catalog = pofile.read_po(buf, domain='mydomain')
        self.assertEqual('mydomain', catalog.domain)

    def test_read_multiline(self):
        buf = StringIO(r'''msgid ""
"Here's some text that\n"
"includesareallylongwordthatmightbutshouldnt"
" throw us into an infinite "
"loop\n"
msgstr ""''')
        catalog = pofile.read_po(buf)
        self.assertEqual(1, len(catalog))
        message = list(catalog)[1]
        self.assertEqual("Here's some text that\nincludesareallylongwordthat"
                         "mightbutshouldnt throw us into an infinite loop\n",
                         message.id)

    def test_fuzzy_header(self):
        buf = StringIO(r'''\
# Translations template for AReallyReallyLongNameForAProject.
# Copyright (C) 2007 ORGANIZATION
# This file is distributed under the same license as the
# AReallyReallyLongNameForAProject project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
#, fuzzy
''')
        catalog = pofile.read_po(buf)
        self.assertEqual(1, len(list(catalog)))
        self.assertEqual(True, list(catalog)[0].fuzzy)

    def test_not_fuzzy_header(self):
        buf = StringIO(r'''\
# Translations template for AReallyReallyLongNameForAProject.
# Copyright (C) 2007 ORGANIZATION
# This file is distributed under the same license as the
# AReallyReallyLongNameForAProject project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
''')
        catalog = pofile.read_po(buf)
        self.assertEqual(1, len(list(catalog)))
        self.assertEqual(False, list(catalog)[0].fuzzy)

    def test_header_entry(self):
        buf = StringIO(r'''\
# SOME DESCRIPTIVE TITLE.
# Copyright (C) 2007 THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version:  3.15\n"
"Report-Msgid-Bugs-To: Fliegender Zirkus <fliegender@zirkus.de>\n"
"POT-Creation-Date: 2007-09-27 11:19+0700\n"
"PO-Revision-Date: 2007-09-27 21:42-0700\n"
"Last-Translator: John <cleese@bavaria.de>\n"
"Language-Team: German Lang <de@babel.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=iso-8859-2\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 1.0dev-r313\n"
''')
        catalog = pofile.read_po(buf)
        self.assertEqual(1, len(list(catalog)))
        self.assertEqual(u'3.15', catalog.version)
        self.assertEqual(u'Fliegender Zirkus <fliegender@zirkus.de>',
                         catalog.msgid_bugs_address)
        self.assertEqual(datetime(2007, 9, 27, 11, 19,
                                  tzinfo=FixedOffsetTimezone(7 * 60)),
                         catalog.creation_date)
        self.assertEqual(u'John <cleese@bavaria.de>', catalog.last_translator)
        self.assertEqual(u'German Lang <de@babel.org>', catalog.language_team)
        self.assertEqual(u'iso-8859-2', catalog.charset)
        self.assertEqual(True, list(catalog)[0].fuzzy)

    def test_obsolete_message(self):
        buf = StringIO(r'''# This is an obsolete message
#~ msgid "foo"
#~ msgstr "Voh"

# This message is not obsolete
#: main.py:1
msgid "bar"
msgstr "Bahr"
''')
        catalog = pofile.read_po(buf)
        self.assertEqual(1, len(catalog))
        self.assertEqual(1, len(catalog.obsolete))
        message = catalog.obsolete[u'foo']
        self.assertEqual(u'foo', message.id)
        self.assertEqual(u'Voh', message.string)
        self.assertEqual(['This is an obsolete message'], message.user_comments)

    def test_obsolete_message_ignored(self):
        buf = StringIO(r'''# This is an obsolete message
#~ msgid "foo"
#~ msgstr "Voh"

# This message is not obsolete
#: main.py:1
msgid "bar"
msgstr "Bahr"
''')
        catalog = pofile.read_po(buf, ignore_obsolete=True)
        self.assertEqual(1, len(catalog))
        self.assertEqual(0, len(catalog.obsolete))

    def test_singlular_plural_form(self):
        buf = StringIO(r'''msgid "foo"
msgid_plural "foo"
msgstr[0] "Voh"
msgstr[1] "Vohs"''') # This is a bad po, ja_JP only uses msgstr[0]
        catalog = pofile.read_po(buf, locale='ja_JP')
        self.assertEqual(1, len(catalog))
        self.assertEqual(1, catalog.num_plurals)
        message = catalog['foo']
        self.assertEqual(1, len(message.string))
        
    def test_more_than_two_plural_forms(self):
        buf = StringIO(r'''msgid "foo"
msgid_plural "foo"
msgstr[0] "Voh"
msgstr[1] "Vohs"''') # last translation form is missing
#msgstr[2] "Vohss"''')
        catalog = pofile.read_po(buf, locale='lv_LV')
        self.assertEqual(1, len(catalog))
        self.assertEqual(3, catalog.num_plurals)
        message = catalog['foo']
        self.assertEqual(3, len(message.string))
        self.assertEqual('', message.string[2])

    def test_plural_with_square_brackets(self):
        buf = StringIO(r'''msgid "foo"
msgid_plural "foos"
msgstr[0] "Voh [text]"
msgstr[1] "Vohs [text]"''')
        catalog = pofile.read_po(buf, locale='nb_NO')
        self.assertEqual(1, len(catalog))
        self.assertEqual(2, catalog.num_plurals)
        message = catalog['foo']
        self.assertEqual(2, len(message.string))


class WritePoTestCase(unittest.TestCase):

    def test_join_locations(self):
        catalog = Catalog()
        catalog.add(u'foo', locations=[('main.py', 1)])
        catalog.add(u'foo', locations=[('utils.py', 3)])
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True)
        self.assertEqual('''#: main.py:1 utils.py:3
msgid "foo"
msgstr ""''', buf.getvalue().strip())

    def test_duplicate_comments(self):
        catalog = Catalog()
        catalog.add(u'foo', auto_comments=['A comment'])
        catalog.add(u'foo', auto_comments=['A comment'])
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True)
        self.assertEqual('''#. A comment
msgid "foo"
msgstr ""''', buf.getvalue().strip())

    def test_wrap_long_lines(self):
        text = """Here's some text where       
white space and line breaks matter, and should

not be removed

"""
        catalog = Catalog()
        catalog.add(text, locations=[('main.py', 1)])
        buf = StringIO()
        pofile.write_po(buf, catalog, no_location=True, omit_header=True,
                         width=42)
        self.assertEqual(r'''msgid ""
"Here's some text where       \n"
"white space and line breaks matter, and"
" should\n"
"\n"
"not be removed\n"
"\n"
msgstr ""''', buf.getvalue().strip())

    def test_wrap_long_lines_with_long_word(self):
        text = """Here's some text that
includesareallylongwordthatmightbutshouldnt throw us into an infinite loop
"""
        catalog = Catalog()
        catalog.add(text, locations=[('main.py', 1)])
        buf = StringIO()
        pofile.write_po(buf, catalog, no_location=True, omit_header=True,
                         width=32)
        self.assertEqual(r'''msgid ""
"Here's some text that\n"
"includesareallylongwordthatmightbutshouldnt"
" throw us into an infinite "
"loop\n"
msgstr ""''', buf.getvalue().strip())
        
    def test_wrap_long_lines_in_header(self):
        """
        Verify that long lines in the header comment are wrapped correctly.
        """
        catalog = Catalog(project='AReallyReallyLongNameForAProject',
                          revision_date=datetime(2007, 4, 1))
        buf = StringIO()
        pofile.write_po(buf, catalog)
        self.assertEqual('''\
# Translations template for AReallyReallyLongNameForAProject.
# Copyright (C) 2007 ORGANIZATION
# This file is distributed under the same license as the
# AReallyReallyLongNameForAProject project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2007.
#
#, fuzzy''', '\n'.join(buf.getvalue().splitlines()[:7]))

    def test_wrap_locations_with_hyphens(self):
        catalog = Catalog()
        catalog.add(u'foo', locations=[
            ('doupy/templates/base/navmenu.inc.html.py', 60)
        ])
        catalog.add(u'foo', locations=[
            ('doupy/templates/job-offers/helpers.html', 22)
        ])
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True)
        self.assertEqual('''#: doupy/templates/base/navmenu.inc.html.py:60
#: doupy/templates/job-offers/helpers.html:22
msgid "foo"
msgstr ""''', buf.getvalue().strip())

    def test_pot_with_translator_comments(self):
        catalog = Catalog()
        catalog.add(u'foo', locations=[('main.py', 1)],
                    auto_comments=['Comment About `foo`'])
        catalog.add(u'bar', locations=[('utils.py', 3)],
                    user_comments=['Comment About `bar` with',
                                   'multiple lines.'])
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True)
        self.assertEqual('''#. Comment About `foo`
#: main.py:1
msgid "foo"
msgstr ""

# Comment About `bar` with
# multiple lines.
#: utils.py:3
msgid "bar"
msgstr ""''', buf.getvalue().strip())

    def test_po_with_obsolete_message(self):
        catalog = Catalog()
        catalog.add(u'foo', u'Voh', locations=[('main.py', 1)])
        catalog.obsolete['bar'] = Message(u'bar', u'Bahr',
                                          locations=[('utils.py', 3)],
                                          user_comments=['User comment'])
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True)
        self.assertEqual('''#: main.py:1
msgid "foo"
msgstr "Voh"

# User comment
#~ msgid "bar"
#~ msgstr "Bahr"''', buf.getvalue().strip())

    def test_po_with_multiline_obsolete_message(self):
        catalog = Catalog()
        catalog.add(u'foo', u'Voh', locations=[('main.py', 1)])
        msgid = r"""Here's a message that covers
multiple lines, and should still be handled
correctly.
"""
        msgstr = r"""Here's a message that covers
multiple lines, and should still be handled
correctly.
"""
        catalog.obsolete[msgid] = Message(msgid, msgstr,
                                          locations=[('utils.py', 3)])
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True)
        self.assertEqual(r'''#: main.py:1
msgid "foo"
msgstr "Voh"

#~ msgid ""
#~ "Here's a message that covers\n"
#~ "multiple lines, and should still be handled\n"
#~ "correctly.\n"
#~ msgstr ""
#~ "Here's a message that covers\n"
#~ "multiple lines, and should still be handled\n"
#~ "correctly.\n"''', buf.getvalue().strip())

    def test_po_with_obsolete_message_ignored(self):
        catalog = Catalog()
        catalog.add(u'foo', u'Voh', locations=[('main.py', 1)])
        catalog.obsolete['bar'] = Message(u'bar', u'Bahr',
                                          locations=[('utils.py', 3)],
                                          user_comments=['User comment'])
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True, ignore_obsolete=True)
        self.assertEqual('''#: main.py:1
msgid "foo"
msgstr "Voh"''', buf.getvalue().strip())

    def test_po_with_previous_msgid(self):
        catalog = Catalog()
        catalog.add(u'foo', u'Voh', locations=[('main.py', 1)],
                    previous_id=u'fo')
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True, include_previous=True)
        self.assertEqual('''#: main.py:1
#| msgid "fo"
msgid "foo"
msgstr "Voh"''', buf.getvalue().strip())

    def test_po_with_previous_msgid_plural(self):
        catalog = Catalog()
        catalog.add((u'foo', u'foos'), (u'Voh', u'Voeh'),
                    locations=[('main.py', 1)], previous_id=(u'fo', u'fos'))
        buf = StringIO()
        pofile.write_po(buf, catalog, omit_header=True, include_previous=True)
        self.assertEqual('''#: main.py:1
#| msgid "fo"
#| msgid_plural "fos"
msgid "foo"
msgid_plural "foos"
msgstr[0] "Voh"
msgstr[1] "Voeh"''', buf.getvalue().strip())

    def test_sorted_po(self):
        catalog = Catalog()
        catalog.add(u'bar', locations=[('utils.py', 3)],
                    user_comments=['Comment About `bar` with',
                                   'multiple lines.'])
        catalog.add((u'foo', u'foos'), (u'Voh', u'Voeh'),
                    locations=[('main.py', 1)])
        buf = StringIO()
        pofile.write_po(buf, catalog, sort_output=True)
        value = buf.getvalue().strip()
        assert '''\
# Comment About `bar` with
# multiple lines.
#: utils.py:3
msgid "bar"
msgstr ""

#: main.py:1
msgid "foo"
msgid_plural "foos"
msgstr[0] "Voh"
msgstr[1] "Voeh"''' in value
        assert value.find('msgid ""') < value.find('msgid "bar"') < value.find('msgid "foo"')

    def test_silent_location_fallback(self):
        buf = StringIO('''\
#: broken_file.py
msgid "missing line number"
msgstr ""

#: broken_file.py:broken_line_number
msgid "broken line number"
msgstr ""''')
        catalog = pofile.read_po(buf)
        self.assertEqual(catalog['missing line number'].locations, [])
        self.assertEqual(catalog['broken line number'].locations, [])

def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(pofile))
    suite.addTest(unittest.makeSuite(ReadPoTestCase))
    suite.addTest(unittest.makeSuite(WritePoTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
