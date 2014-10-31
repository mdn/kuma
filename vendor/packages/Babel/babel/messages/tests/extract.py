# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

import codecs
import doctest
from StringIO import StringIO
import sys
import unittest

from babel.messages import extract


class ExtractPythonTestCase(unittest.TestCase):

    def test_nested_calls(self):
        buf = StringIO("""\
msg1 = _(i18n_arg.replace(r'\"', '"'))
msg2 = ungettext(i18n_arg.replace(r'\"', '"'), multi_arg.replace(r'\"', '"'), 2)
msg3 = ungettext("Babel", multi_arg.replace(r'\"', '"'), 2)
msg4 = ungettext(i18n_arg.replace(r'\"', '"'), "Babels", 2)
msg5 = ungettext('bunny', 'bunnies', random.randint(1, 2))
msg6 = ungettext(arg0, 'bunnies', random.randint(1, 2))
msg7 = _(hello.there)
msg8 = gettext('Rabbit')
msg9 = dgettext('wiki', model.addPage())
msg10 = dngettext(getDomain(), 'Page', 'Pages', 3)
""")
        messages = list(extract.extract_python(buf,
                                               extract.DEFAULT_KEYWORDS.keys(),
                                               [], {}))
        self.assertEqual([
                (1, '_', None, []),
                (2, 'ungettext', (None, None, None), []),
                (3, 'ungettext', (u'Babel', None, None), []),
                (4, 'ungettext', (None, u'Babels', None), []),
                (5, 'ungettext', (u'bunny', u'bunnies', None), []),
                (6, 'ungettext', (None, u'bunnies', None), []),
                (7, '_', None, []),
                (8, 'gettext', u'Rabbit', []),
                (9, 'dgettext', (u'wiki', None), []),
                (10, 'dngettext', (None, u'Page', u'Pages', None), [])],
                         messages)

    def test_nested_comments(self):
        buf = StringIO("""\
msg = ngettext('pylon',  # TRANSLATORS: shouldn't be
               'pylons', # TRANSLATORS: seeing this
               count)
""")
        messages = list(extract.extract_python(buf, ('ngettext',),
                                               ['TRANSLATORS:'], {}))
        self.assertEqual([(1, 'ngettext', (u'pylon', u'pylons', None), [])],
                         messages)

    def test_comments_with_calls_that_spawn_multiple_lines(self):
        buf = StringIO("""\
# NOTE: This Comment SHOULD Be Extracted
add_notice(req, ngettext("Catalog deleted.",
                         "Catalogs deleted.", len(selected)))

# NOTE: This Comment SHOULD Be Extracted
add_notice(req, _("Locale deleted."))


# NOTE: This Comment SHOULD Be Extracted
add_notice(req, ngettext("Foo deleted.", "Foos deleted.", len(selected)))

# NOTE: This Comment SHOULD Be Extracted
# NOTE: And This One Too
add_notice(req, ngettext("Bar deleted.",
                         "Bars deleted.", len(selected)))
""")
        messages = list(extract.extract_python(buf, ('ngettext','_'), ['NOTE:'],

                                               {'strip_comment_tags':False}))
        self.assertEqual((6, '_', 'Locale deleted.',
                          [u'NOTE: This Comment SHOULD Be Extracted']),
                         messages[1])
        self.assertEqual((10, 'ngettext', (u'Foo deleted.', u'Foos deleted.',
                                           None),
                          [u'NOTE: This Comment SHOULD Be Extracted']),
                         messages[2])
        self.assertEqual((3, 'ngettext',
                           (u'Catalog deleted.',
                            u'Catalogs deleted.', None),
                           [u'NOTE: This Comment SHOULD Be Extracted']),
                         messages[0])
        self.assertEqual((15, 'ngettext', (u'Bar deleted.', u'Bars deleted.',
                                           None),
                          [u'NOTE: This Comment SHOULD Be Extracted',
                           u'NOTE: And This One Too']),
                         messages[3])

    def test_declarations(self):
        buf = StringIO("""\
class gettext(object):
    pass
def render_body(context,x,y=_('Page arg 1'),z=_('Page arg 2'),**pageargs):
    pass
def ngettext(y='arg 1',z='arg 2',**pageargs):
    pass
class Meta:
    verbose_name = _('log entry')
""")
        messages = list(extract.extract_python(buf,
                                               extract.DEFAULT_KEYWORDS.keys(),
                                               [], {}))
        self.assertEqual([(3, '_', u'Page arg 1', []),
                          (3, '_', u'Page arg 2', []),
                          (8, '_', u'log entry', [])],
                         messages)

    def test_multiline(self):
        buf = StringIO("""\
msg1 = ngettext('pylon',
                'pylons', count)
msg2 = ngettext('elvis',
                'elvises',
                 count)
""")
        messages = list(extract.extract_python(buf, ('ngettext',), [], {}))
        self.assertEqual([(1, 'ngettext', (u'pylon', u'pylons', None), []),
                          (3, 'ngettext', (u'elvis', u'elvises', None), [])],
                         messages)

    def test_triple_quoted_strings(self):
        buf = StringIO("""\
msg1 = _('''pylons''')
msg2 = ngettext(r'''elvis''', \"\"\"elvises\"\"\", count)
msg2 = ngettext(\"\"\"elvis\"\"\", 'elvises', count)
""")
        messages = list(extract.extract_python(buf,
                                               extract.DEFAULT_KEYWORDS.keys(),
                                               [], {}))
        self.assertEqual([(1, '_', (u'pylons'), []),
                          (2, 'ngettext', (u'elvis', u'elvises', None), []),
                          (3, 'ngettext', (u'elvis', u'elvises', None), [])],
                         messages)

    def test_multiline_strings(self):
        buf = StringIO("""\
_('''This module provides internationalization and localization
support for your Python programs by providing an interface to the GNU
gettext message catalog library.''')
""")
        messages = list(extract.extract_python(buf,
                                               extract.DEFAULT_KEYWORDS.keys(),
                                               [], {}))
        self.assertEqual(
            [(1, '_',
              u'This module provides internationalization and localization\n'
              'support for your Python programs by providing an interface to '
              'the GNU\ngettext message catalog library.', [])],
            messages)

    def test_concatenated_strings(self):
        buf = StringIO("""\
foobar = _('foo' 'bar')
""")
        messages = list(extract.extract_python(buf,
                                               extract.DEFAULT_KEYWORDS.keys(),
                                               [], {}))
        self.assertEqual(u'foobar', messages[0][2])

    def test_unicode_string_arg(self):
        buf = StringIO("msg = _(u'Foo Bar')")
        messages = list(extract.extract_python(buf, ('_',), [], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])

    def test_comment_tag(self):
        buf = StringIO("""
# NOTE: A translation comment
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])
        self.assertEqual([u'NOTE: A translation comment'], messages[0][3])

    def test_comment_tag_multiline(self):
        buf = StringIO("""
# NOTE: A translation comment
# with a second line
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])
        self.assertEqual([u'NOTE: A translation comment', u'with a second line'],
                         messages[0][3])

    def test_translator_comments_with_previous_non_translator_comments(self):
        buf = StringIO("""
# This shouldn't be in the output
# because it didn't start with a comment tag
# NOTE: A translation comment
# with a second line
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])
        self.assertEqual([u'NOTE: A translation comment', u'with a second line'],
                         messages[0][3])

    def test_comment_tags_not_on_start_of_comment(self):
        buf = StringIO("""
# This shouldn't be in the output
# because it didn't start with a comment tag
# do NOTE: this will not be a translation comment
# NOTE: This one will be
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])
        self.assertEqual([u'NOTE: This one will be'], messages[0][3])

    def test_multiple_comment_tags(self):
        buf = StringIO("""
# NOTE1: A translation comment for tag1
# with a second line
msg = _(u'Foo Bar1')

# NOTE2: A translation comment for tag2
msg = _(u'Foo Bar2')
""")
        messages = list(extract.extract_python(buf, ('_',),
                                               ['NOTE1:', 'NOTE2:'], {}))
        self.assertEqual(u'Foo Bar1', messages[0][2])
        self.assertEqual([u'NOTE1: A translation comment for tag1',
                          u'with a second line'], messages[0][3])
        self.assertEqual(u'Foo Bar2', messages[1][2])
        self.assertEqual([u'NOTE2: A translation comment for tag2'], messages[1][3])

    def test_two_succeeding_comments(self):
        buf = StringIO("""
# NOTE: one
# NOTE: two
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])
        self.assertEqual([u'NOTE: one', u'NOTE: two'], messages[0][3])

    def test_invalid_translator_comments(self):
        buf = StringIO("""
# NOTE: this shouldn't apply to any messages
hello = 'there'

msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])
        self.assertEqual([], messages[0][3])

    def test_invalid_translator_comments2(self):
        buf = StringIO("""
# NOTE: Hi!
hithere = _('Hi there!')

# NOTE: you should not be seeing this in the .po
rows = [[v for v in range(0,10)] for row in range(0,10)]

# this (NOTE:) should not show up either
hello = _('Hello')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Hi there!', messages[0][2])
        self.assertEqual([u'NOTE: Hi!'], messages[0][3])
        self.assertEqual(u'Hello', messages[1][2])
        self.assertEqual([], messages[1][3])

    def test_invalid_translator_comments3(self):
        buf = StringIO("""
# NOTE: Hi,

# there!
hithere = _('Hi there!')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Hi there!', messages[0][2])
        self.assertEqual([], messages[0][3])

    def test_comment_tag_with_leading_space(self):
        buf = StringIO("""
  #: A translation comment
  #: with leading spaces
msg = _(u'Foo Bar')
""")
        messages = list(extract.extract_python(buf, ('_',), [':'], {}))
        self.assertEqual(u'Foo Bar', messages[0][2])
        self.assertEqual([u': A translation comment', u': with leading spaces'],
                         messages[0][3])

    def test_different_signatures(self):
        buf = StringIO("""
foo = _('foo', 'bar')
n = ngettext('hello', 'there', n=3)
n = ngettext(n=3, 'hello', 'there')
n = ngettext(n=3, *messages)
n = ngettext()
n = ngettext('foo')
""")
        messages = list(extract.extract_python(buf, ('_', 'ngettext'), [], {}))
        self.assertEqual((u'foo', u'bar'), messages[0][2])
        self.assertEqual((u'hello', u'there', None), messages[1][2])
        self.assertEqual((None, u'hello', u'there'), messages[2][2])
        self.assertEqual((None, None), messages[3][2])
        self.assertEqual(None, messages[4][2])
        self.assertEqual(('foo'), messages[5][2])

    def test_utf8_message(self):
        buf = StringIO("""
# NOTE: hello
msg = _('Bonjour à tous')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'],
                                               {'encoding': 'utf-8'}))
        self.assertEqual(u'Bonjour à tous', messages[0][2])
        self.assertEqual([u'NOTE: hello'], messages[0][3])

    def test_utf8_message_with_magic_comment(self):
        buf = StringIO("""# -*- coding: utf-8 -*-
# NOTE: hello
msg = _('Bonjour à tous')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Bonjour à tous', messages[0][2])
        self.assertEqual([u'NOTE: hello'], messages[0][3])

    def test_utf8_message_with_utf8_bom(self):
        buf = StringIO(codecs.BOM_UTF8 + """
# NOTE: hello
msg = _('Bonjour à tous')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Bonjour à tous', messages[0][2])
        self.assertEqual([u'NOTE: hello'], messages[0][3])

    def test_utf8_raw_strings_match_unicode_strings(self):
        buf = StringIO(codecs.BOM_UTF8 + """
msg = _('Bonjour à tous')
msgu = _(u'Bonjour à tous')
""")
        messages = list(extract.extract_python(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Bonjour à tous', messages[0][2])
        self.assertEqual(messages[0][2], messages[1][2])

    def test_extract_strip_comment_tags(self):
        buf = StringIO("""\
#: This is a comment with a very simple
#: prefix specified
_('Servus')

# NOTE: This is a multiline comment with
# a prefix too
_('Babatschi')""")
        messages = list(extract.extract('python', buf, comment_tags=['NOTE:', ':'],
                                        strip_comment_tags=True))
        self.assertEqual(u'Servus', messages[0][1])
        self.assertEqual([u'This is a comment with a very simple',
                          u'prefix specified'], messages[0][2])
        self.assertEqual(u'Babatschi', messages[1][1])
        self.assertEqual([u'This is a multiline comment with',
                          u'a prefix too'], messages[1][2])


class ExtractJavaScriptTestCase(unittest.TestCase):

    def test_simple_extract(self):
        buf = StringIO("""\
msg1 = _('simple')
msg2 = gettext('simple')
msg3 = ngettext('s', 'p', 42)
        """)
        messages = \
            list(extract.extract('javascript', buf, extract.DEFAULT_KEYWORDS,
                                 [], {}))

        self.assertEqual([(1, 'simple', []),
                          (2, 'simple', []),
                          (3, ('s', 'p'), [])], messages)

    def test_various_calls(self):
        buf = StringIO("""\
msg1 = _(i18n_arg.replace(/"/, '"'))
msg2 = ungettext(i18n_arg.replace(/"/, '"'), multi_arg.replace(/"/, '"'), 2)
msg3 = ungettext("Babel", multi_arg.replace(/"/, '"'), 2)
msg4 = ungettext(i18n_arg.replace(/"/, '"'), "Babels", 2)
msg5 = ungettext('bunny', 'bunnies', parseInt(Math.random() * 2 + 1))
msg6 = ungettext(arg0, 'bunnies', rparseInt(Math.random() * 2 + 1))
msg7 = _(hello.there)
msg8 = gettext('Rabbit')
msg9 = dgettext('wiki', model.addPage())
msg10 = dngettext(domain, 'Page', 'Pages', 3)
""")
        messages = \
            list(extract.extract('javascript', buf, extract.DEFAULT_KEYWORDS, [],
                                 {}))
        self.assertEqual([(5, (u'bunny', u'bunnies'), []),
                          (8, u'Rabbit', []),
                          (10, (u'Page', u'Pages'), [])], messages)

    def test_message_with_line_comment(self):
        buf = StringIO("""\
// NOTE: hello
msg = _('Bonjour à tous')
""")
        messages = list(extract.extract_javascript(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Bonjour à tous', messages[0][2])
        self.assertEqual([u'NOTE: hello'], messages[0][3])

    def test_message_with_multiline_comment(self):
        buf = StringIO("""\
/* NOTE: hello
   and bonjour
     and servus */
msg = _('Bonjour à tous')
""")
        messages = list(extract.extract_javascript(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Bonjour à tous', messages[0][2])
        self.assertEqual([u'NOTE: hello', 'and bonjour', '  and servus'], messages[0][3])

    def test_ignore_function_definitions(self):
        buf = StringIO("""\
function gettext(value) {
    return translations[language][value] || value;
}""")

        messages = list(extract.extract_javascript(buf, ('gettext',), [], {}))
        self.assertEqual(messages, [])

    def test_misplaced_comments(self):
        buf = StringIO("""\
/* NOTE: this won't show up */
foo()

/* NOTE: this will */
msg = _('Something')

// NOTE: this will show up
// too.
msg = _('Something else')

// NOTE: but this won't
bar()

_('no comment here')
""")
        messages = list(extract.extract_javascript(buf, ('_',), ['NOTE:'], {}))
        self.assertEqual(u'Something', messages[0][2])
        self.assertEqual([u'NOTE: this will'], messages[0][3])
        self.assertEqual(u'Something else', messages[1][2])
        self.assertEqual([u'NOTE: this will show up', 'too.'], messages[1][3])
        self.assertEqual(u'no comment here', messages[2][2])
        self.assertEqual([], messages[2][3])


class ExtractTestCase(unittest.TestCase):

    def test_invalid_filter(self):
        buf = StringIO("""\
msg1 = _(i18n_arg.replace(r'\"', '"'))
msg2 = ungettext(i18n_arg.replace(r'\"', '"'), multi_arg.replace(r'\"', '"'), 2)
msg3 = ungettext("Babel", multi_arg.replace(r'\"', '"'), 2)
msg4 = ungettext(i18n_arg.replace(r'\"', '"'), "Babels", 2)
msg5 = ungettext('bunny', 'bunnies', random.randint(1, 2))
msg6 = ungettext(arg0, 'bunnies', random.randint(1, 2))
msg7 = _(hello.there)
msg8 = gettext('Rabbit')
msg9 = dgettext('wiki', model.addPage())
msg10 = dngettext(domain, 'Page', 'Pages', 3)
""")
        messages = \
            list(extract.extract('python', buf, extract.DEFAULT_KEYWORDS, [],
                                 {}))
        self.assertEqual([(5, (u'bunny', u'bunnies'), []),
                          (8, u'Rabbit', []),
                          (10, (u'Page', u'Pages'), [])], messages)

    def test_invalid_extract_method(self):
        buf = StringIO('')
        self.assertRaises(ValueError, list, extract.extract('spam', buf))

    def test_different_signatures(self):
        buf = StringIO("""
foo = _('foo', 'bar')
n = ngettext('hello', 'there', n=3)
n = ngettext(n=3, 'hello', 'there')
n = ngettext(n=3, *messages)
n = ngettext()
n = ngettext('foo')
""")
        messages = \
            list(extract.extract('python', buf, extract.DEFAULT_KEYWORDS, [],
                                 {}))
        self.assertEqual(len(messages), 2)
        self.assertEqual(u'foo', messages[0][1])
        self.assertEqual((u'hello', u'there'), messages[1][1])

    def test_empty_string_msgid(self):
        buf = StringIO("""\
msg = _('')
""")
        stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            messages = \
                list(extract.extract('python', buf, extract.DEFAULT_KEYWORDS,
                                     [], {}))
            self.assertEqual([], messages)
            assert 'warning: Empty msgid.' in sys.stderr.getvalue()
        finally:
            sys.stderr = stderr


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(extract))
    suite.addTest(unittest.makeSuite(ExtractPythonTestCase))
    suite.addTest(unittest.makeSuite(ExtractJavaScriptTestCase))
    suite.addTest(unittest.makeSuite(ExtractTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
