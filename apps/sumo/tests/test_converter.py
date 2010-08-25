from nose.tools import eq_

from sumo.converter import TikiMarkupConverter
from sumo.tests import TestCase


converter = TikiMarkupConverter()


class TestConverter(TestCase):

    def test_bold(self):
        content = '__bold__'
        eq_("'''bold'''", converter.convert(content))

    def test_italics(self):
        content = "''italics''"
        eq_("''italics''", converter.convert(content))

    def test_bold_and_italics(self):
        content = "''__bold and italics__''"
        eq_("'''''bold and italics'''''", converter.convert(content))

    def test_internal_link(self):
        content = '((Internal link))'
        eq_('[[Internal link]]', converter.convert(content))

    def test_internal_link_named(self):
        content = '((Internal link|link name))'
        eq_('[[Internal link|link name]]', converter.convert(content))

    def test_internal_link_multiple(self):
        content = '((Internal link)) and ((Internal again|named))'
        eq_('[[Internal link]] and [[Internal again|named]]',
            converter.convert(content))
        content = '((Internal link|named)) and ((Internal again))'
        eq_('[[Internal link|named]] and [[Internal again]]',
            converter.convert(content))

    def test_external_link(self):
        content = '[http://external.link]'
        eq_('[http://external.link]', converter.convert(content))
        content = '[http://external.link|named]'
        eq_('[http://external.link named]', converter.convert(content))

    def test_heading(self):
        content = """!heading 1
                     \n!! heading 2
                     \n!!! heading 3
                     \n!!!!heading 4
                     \n!!!!! heading 5
                     \n!!!!!! heading 6"""
        expected = """= heading 1 =
                     \n== heading 2 ==
                     \n=== heading 3 ===
                     \n==== heading 4 ====
                     \n===== heading 5 =====
                     \n====== heading 6 ======"""
        eq_(expected, converter.convert(content))

    def test_underline(self):
        content = '===underlined text==='
        eq_('<u>underlined text</u>', converter.convert(content))

    def test_horizontal_line_3(self):
        # 4 dashes stays the same
        content = 'Some text\n----\nmore text'
        eq_('Some text\n----\nmore text', converter.convert(content))
        # 3 dashes are turned into 4
        content = 'Some text\n---\nmore text'
        eq_('Some text\n----\nmore text', converter.convert(content))

    def test_code(self):
        content = '{CODE()}\nthis is code\n{CODE}'
        eq_('<code>\nthis is code\n</code>', converter.convert(content))

    def test_remove_not_allowed_plugins(self):
        content = 'lala\n{maketoc} \nblarg\n{ANAME()}This is an ANAME{ANAME}'
        eq_('lala\n  \nblarg\n This is an ANAME ',
            converter.convert(content))
        content = '{SPAN()}something{SPAN}{DIV()} blah{DIV}'
        eq_(' something   blah ', converter.convert(content))
        content = '{DIV(class=nomac)}something{DIV}'
        eq_(' something ', converter.convert(content))

    def test_remove_percents(self):
        content = '# lala  %%% line break'
        eq_('# lala  <br/> line break', converter.convert(content))

    def test_remove_comments(self):
        content = '~np~((Basic Troubleshooting|#Clean reinstall)) ~/np~'
        eq_(' [[Basic Troubleshooting|#Clean reinstall]]  ',
            converter.convert(content))
        content = '~tc~((Basic Troubleshooting)) ~/tc~'
        eq_(' [[Basic Troubleshooting]]  ', converter.convert(content))

    def test_blockquote(self):
        content = '^ a multiline\n blockquote ^'
        eq_('<blockquote> a multiline\n blockquote </blockquote>',
            converter.convert(content))

    def test_unicode(self):
        # French
        content = u'((Vous parl\u00e9 Fran\u00e7ais)). \n* Tr\u00e9s bien.'
        eq_(u'[[Vous parl\u00e9 Fran\u00e7ais]]. \n* Tr\u00e9s bien.',
            converter.convert(content))
        # Japanese
        content = u'!! \u6709\u52b9'
        eq_(u'== \u6709\u52b9 ==', converter.convert(content))

    def test_basic(self):
        """Basic functionality works."""
        content = """In [http://article.com|this article] he mentioned that
                     he found that certain proxy settings can cause a
                     ((Firefox never finishes loading certain websites))
                     condition.

                    Here's what we have now:
                    * ((Server not found)): %%% Just links to ((Firefox))
                    * ((Cannot connect after upgrading)) %%% Blah"""

        expected = """In [http://article.com this article] he mentioned that
                     he found that certain proxy settings can cause a
                     [[Firefox never finishes loading certain websites]]
                     condition.

                    Here's what we have now:
                    * [[Server not found]]: <br/> Just links to [[Firefox]]
                    * [[Cannot connect after upgrading]] <br/> Blah"""

        eq_(expected, converter.convert(content))
