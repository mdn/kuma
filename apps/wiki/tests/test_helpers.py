from nose.tools import eq_
from test_utils import TestCase

from wiki.helpers import get_seo_description


class GetSEODescriptionTests(TestCase):

    def test_html_elements_spaces(self):
        # No spaces with html tags
        content = (u'<p><span class="seoSummary">The <strong>Document Object '
             'Model'
             '</strong> (<strong>DOM</strong>) is an API for '
             '<a href="/en-US/docs/HTML" title="en-US/docs/HTML">HTML</a> and '
             '<a href="/en-US/docs/XML" title="en-US/docs/XML">XML</a> '
             'documents. It provides a structural representation of the '
             'document, enabling you to modify its content and visual '
             'presentation by using a scripting language such as '
             '<a href="/en-US/docs/JavaScript" '
             'title="https://developer.mozilla.org/en-US/docs/JavaScript">'
             'JavaScript</a>.</span></p>')
        expected = ('The Document Object Model (DOM) is an API for HTML and '
            'XML'
            ' documents. It provides a structural representation of the'
            ' document, enabling you to modify its content and visual'
            ' presentation by using a scripting language such as'
            ' JavaScript.')
        eq_(expected, get_seo_description(content, 'en-US'))

        content = (u'<p><span class="seoSummary"><strong>Cascading Style '
                   'Sheets</strong>, most of the time abbreviated in '
                   '<strong>CSS</strong>, is a '
                   '<a href="/en-US/docs/DOM/stylesheet">stylesheet</a> '
                   'language used to describe the presentation of a document '
                   'written in <a href="/en-US/docs/HTML" title="The '
                   'HyperText Mark-up Language">HTML</a></span> or <a '
                   'href="/en-US/docs/XML" title="en-US/docs/XML">XML</a> '
                   '(including various XML languages like <a '
                   'href="/en-US/docs/SVG" title="en-US/docs/SVG">SVG</a> or '
                   '<a href="/en-US/docs/XHTML" '
                   'title="en-US/docs/XHTML">XHTML</a>)<span '
                   'class="seoSummary">. CSS describes how the structured '
                   'element must be rendered on screen, on paper, in speech, '
                   'or on other media.</span></p>')
        expected = ('Cascading Style Sheets, most of the time abbreviated in '
                    'CSS, is a stylesheet language used to describe the '
                    'presentation of a document written in HTML. CSS '
                    'describes how the structured element must be rendered on '
                    'screen, on paper, in speech, or on other media.')
        eq_(expected, get_seo_description(content, 'en-US'))
