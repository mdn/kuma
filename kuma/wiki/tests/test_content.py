# -*- coding: utf-8 -*-
from base64 import b64encode

import bleach
import pytest
from django.conf import settings
from django.test import TestCase
from django.utils.six.moves.urllib.parse import urljoin
from jinja2 import escape, Markup
from pyquery import PyQuery as pq

import kuma.wiki.content

from . import document, normalize_html
from ..constants import ALLOWED_ATTRIBUTES, ALLOWED_PROTOCOLS, ALLOWED_TAGS
from ..content import (clean_content, CodeSyntaxFilter, get_content_sections,
                       get_seo_description, H2TOCFilter, H3TOCFilter, parse,
                       SECTION_TAGS, SectionIDFilter, SectionTOCFilter)
from ..models import Document, Revision
from ..templatetags.jinja_helpers import bugize_text

AL_BASE_URL = 'https://example.com'  # Base URL for annotateLinks tests

EMPTY_IFRAME = '<iframe></iframe>'
SUMMARY_DOM_MARKUP = (
    'The <strong>Document Object Model</strong> (<strong>DOM</strong>) is an '
    'API for <a href="/en-US/docs/HTML" title="en-US/docs/HTML">HTML</a> and '
    '<a href="/en-US/docs/XML" title="en-US/docs/XML">XML</a> documents. It '
    'provides a structural representation of the document, enabling you to '
    'modify its content and visual presentation by using a scripting language '
    'such as <a href="/en-US/docs/JavaScript" title='
    '"https://developer.mozilla.org/en-US/docs/JavaScript">JavaScript</a>.'
)
SUMMARY_DOM_TEXT = (
    'The Document Object Model (DOM) is an API for HTML and XML documents. '
    'It provides a structural representation of the document, enabling you '
    'to modify its content and visual presentation by using a scripting '
    'language such as JavaScript.'
)
SUMMARIES_SEO_MARKUP_PART1 = (
    '<strong>Cascading Style Sheets</strong>, most of the time abbreviated '
    'in <strong>CSS</strong>, is a <a href="/en-US/docs/DOM/stylesheet">'
    'stylesheet</a> language used to describe the presentation of a document '
    'written in <a href="/en-US/docs/HTML" '
    'title="The HyperText Mark-up Language">HTML</a>'
)
SUMMARIES_SEO_MARKUP_PART2 = (
    '. CSS describes how the structured element must be rendered on screen, '
    'on paper, in speech, or on other media.'
)
SUMMARIES_SEO_MARKUP_FORMAT = (
    '<span class="seoSummary">{0}</span> or <a href="/en-US/docs/XML" '
    'title="en-US/docs/XML">XML</a> (including various XML languages like '
    '<a href="/en-US/docs/SVG" title="en-US/docs/SVG">SVG</a> or '
    '<a href="/en-US/docs/XHTML" title="en-US/docs/XHTML">XHTML</a>)'
    '<span class="seoSummary">{1}</span>'
)
SUMMARIES_SEO_TEXT = (
    'Cascading Style Sheets, most of the time abbreviated in CSS, is a '
    'stylesheet language used to describe the presentation of a document '
    'written in HTML. CSS describes how the structured element must be '
    'rendered on screen, on paper, in speech, or on other media.'
)
SUMMARY_WRAPPERS = {
    'no_summary_section': '<p>{}</p>',
    'summary_section': '<h2 id="Summary">Summary</h2><p>{}</p>',
}
SUMMARY_PLUS_SEO_WRAPPERS = dict(
    SUMMARY_WRAPPERS,
    no_summary_section_plus_seo='<p><span class="seoSummary">{}</span></p>',
    summary_section_plus_seo=(
        '<h2 id="Summary">Summary</h2><p>Some other text</p>'
        '<p><span class="seoSummary">{}</span></p>'
    ),
)
SUMMARY_CONTENT = {
    'without_empty_iframe': (SUMMARY_DOM_MARKUP, SUMMARY_DOM_TEXT),
    'with_empty_iframe': (EMPTY_IFRAME + SUMMARY_DOM_MARKUP, SUMMARY_DOM_TEXT),
}
SUMMARIES_SEO_CONTENT = {
    'with_empty_iframe': (
        SUMMARIES_SEO_MARKUP_FORMAT.format(
            EMPTY_IFRAME + SUMMARIES_SEO_MARKUP_PART1,
            EMPTY_IFRAME + SUMMARIES_SEO_MARKUP_PART2
        ),
        (EMPTY_IFRAME + SUMMARIES_SEO_MARKUP_PART1 +
         EMPTY_IFRAME + SUMMARIES_SEO_MARKUP_PART2),
        SUMMARIES_SEO_TEXT
    ),
    'without_empty_iframe': (
        SUMMARIES_SEO_MARKUP_FORMAT.format(
            SUMMARIES_SEO_MARKUP_PART1,
            SUMMARIES_SEO_MARKUP_PART2
        ),
        SUMMARIES_SEO_MARKUP_PART1 + SUMMARIES_SEO_MARKUP_PART2,
        SUMMARIES_SEO_TEXT
    ),
}


class GetContentSectionsTests(TestCase):
    def test_section_pars_for_empty_docs(self):
        doc = document(title='Doc', locale=u'fr', slug=u'doc', save=True,
                       html='<!-- -->')
        res = get_content_sections(doc.html)
        assert 'list' == type(res).__name__


class InjectSectionIDsTests(TestCase):
    def test_section_ids(self):

        doc_src = """
            <h1 class="header1">Header One</h1>
            <p>test</p>
            <section>
                <h1 class="header2">Header Two</h1>
                <h1 name="Header: X" class="header3">Header Three</h1>
                <p>test</p>
            </section>
            <h2 name="C~o:n;s/t%a$n=t@s" class="hasname">This is ignored</h2>
            <p>test</p>

            <h1 id="i-already-have-an-id" class="hasid">This text clobbers the ID</h1>

            <h1 class="header3">Header Three</h1>
            <p>test</p>

            <section id="Quick_Links" class="Quick_Links">
                <ol>
                    <li>Hey look, quick links</li>
                </ol>
            </section>
        """

        result_src = (kuma.wiki.content
                      .parse(doc_src)
                      .injectSectionIDs()
                      .serialize())
        result_doc = pq(result_src)

        expected = (
            ('header1', 'Header_One'),
            ('header2', 'Header_Two'),
            ('header3', 'Header_X'),
            ('hasname', 'Constants'),
            ('hasid', 'This_text_clobbers_the_ID'),
            ('Quick_Links', 'Quick_Links'),
        )
        for cls, id in expected:
            assert id == result_doc.find('.%s' % cls).attr('id')

        # Then, ensure all elements in need of an ID now all have unique IDs.
        assert len(SECTION_TAGS)
        els = result_doc.find(', '.join(SECTION_TAGS))
        seen_ids = set()
        for i in range(0, len(els)):
            id = els.eq(i).attr('id')
            assert id is not None
            assert id not in seen_ids
            seen_ids.add(id)

    def test_incremented_section_ids(self):

        doc_src = """
        <h1 class="header1">Header One</h1>
        <h1>Header One</h1>
        <h1>Header One</h1>
        <h1>Header Two</h1>
        <h1 name="someId">Header Two</h1>
        """

        result_src = (kuma.wiki.content
                      .parse(doc_src)
                      .injectSectionIDs()
                      .serialize())

        expected = """
        <h1 id="Header_One" class="header1">Header One</h1>
        <h1 id="Header_One_2">Header One</h1>
        <h1 id="Header_One_3">Header One</h1>
        <h1 id="Header_Two">Header Two</h1>
        <h1 id="someId" name="someId">Header Two</h1>
        """

        self.assertHTMLEqual(result_src, expected)

        # Ensure 1, 2 doesn't turn into 3, 4
        result_src = (kuma.wiki.content
                      .parse(expected)
                      .injectSectionIDs()
                      .serialize())
        self.assertHTMLEqual(result_src, expected)


def test_extractSection_by_header_id():
    """extractSection can extract by header element id."""
    doc_src = """
        <h1 id="s1">Head 1</h1><p>test 1</p>
        <h1 id="s2">Head 2</h1><p>test 2</p>
    """
    expected = """
        <h1 id="s1">Head 1</h1><p>test 1</p>
    """
    result = parse(doc_src).extractSection(id="s1").serialize()
    assert normalize_html(result) == normalize_html(expected)


def test_extractSection_heading_in_section():
    """extractSection can extract a header inside a section."""
    doc_src = """
        <h1 id="s4">Head</h1><p>test</p>
        <section id="parent-s5">
          <h1 id="s5">Head 5</h1>
            <p>test</p>
            <section>
              <h1>head subsection</h1>
            </section>
          <h2 id="s5-1">Head 5-1</h2><p>test</p>
          <h1 id="s5-next">Head 5 next</h1><p>test</p>
        </section>
        <h1 id="s7">Head 7</h1><p>test</p>
    """
    expected = """
          <h1 id="s5">Head 5</h1>
            <p>test</p>
            <section>
              <h1>head subsection</h1>
            </section>
          <h2 id="s5-1">Head 5-1</h2><p>test</p>
    """  # h1 and h2, but not the next h1
    result = parse(doc_src).extractSection(id="s5").serialize()
    assert normalize_html(result) == normalize_html(expected)


def test_extractSection_by_section():
    """extractSection can extract the contents of a section."""
    doc_src = """
        <h1 id="s4">Head</h1><p>test</p>
        <section id="parent-s5">
          <h1 id="s5">Head 5</h1>
            <p>test</p>
            <section>
              <h1>head subsection</h1>
            </section>
          <h2 id="s5-1">Head 5-1</h2><p>test</p>
          <h1 id="s5-next">Head 5 next</h1><p>test</p>
        </section>
        <h1 id="s7">Head 7</h1><p>test</p>
    """  # Same as test_extractSection_heading_in_section
    expected = """
          <h1 id="s5">Head 5</h1>
            <p>test</p>
            <section>
              <h1>head subsection</h1>
            </section>
          <h2 id="s5-1">Head 5-1</h2><p>test</p>
          <h1 id="s5-next">Head 5 next</h1><p>test</p>
    """  # All headings inside the section
    result = parse(doc_src).extractSection(id="parent-s5").serialize()
    assert normalize_html(result) == normalize_html(expected)


def test_extractSection_descending_heading_levels():
    """extractSection extracts simple sub-headings."""
    doc_src = """
        <p>test</p>
        <h1 id="s4">Head 4</h1><p>test 4</p>
        <h2 id="s4-1">Head 4-1</h2><p>test 4-1</p>
        <h3 id="s4-2">Head 4-1-1</h3><p>test 4-2</p>
        <h1 id="s4-next">Head</h1><p>test next</p>
    """
    expected = """
        <h1 id="s4">Head 4</h1><p>test 4</p>
        <h2 id="s4-1">Head 4-1</h2><p>test 4-1</p>
        <h3 id="s4-2">Head 4-1-1</h3><p>test 4-2</p>
    """  # All headings up to the next h1
    result = parse(doc_src).extractSection(id="s4").serialize()
    assert normalize_html(result) == normalize_html(expected)


def test_extractSection_complex_heading_levels():
    """extractSection extracts complex sub-headings."""
    doc_src = """
        <h1 id="s7">Head 7</h1><p>test 7</p>
        <h1 id="s8">Head</h1><p>test 8</p>
        <h2 id="s8-1">Head</h1><p>test 8-1</p>
        <h3 id="s8-1-1">Head</h3><p>test 8-1-1</p>
        <h2 id="s8-2">Head</h1><p>test 8-2</p>
        <h3 id="s8-2-1">Head</h3><p>test 8-2-1</p>
        <h4 id="s8-2-1-1">Head</h4><p>test 8-2-1-1</p>
        <h2 id="s8-3">Head</h1><p>test 8-3</p>
        <h1 id="s9">Head</h1><p>test 9</p>
    """
    expected = """
        <h1 id="s8">Head</h1><p>test 8</p>
        <h2 id="s8-1">Head</h1><p>test 8-1</p>
        <h3 id="s8-1-1">Head</h3><p>test 8-1-1</p>
        <h2 id="s8-2">Head</h1><p>test 8-2</p>
        <h3 id="s8-2-1">Head</h3><p>test 8-2-1</p>
        <h4 id="s8-2-1-1">Head</h4><p>test 8-2-1-1</p>
        <h2 id="s8-3">Head</h1><p>test 8-3</p>
    """  # All headings up to the next h1
    result = parse(doc_src).extractSection(id="s8").serialize()
    assert normalize_html(result) == normalize_html(expected)


def test_extractSection_ignore_heading():
    """extractSection can exclude the header element."""
    doc_src = """
        <p>test</p>
        <h1 id="s4">Head 4</h1><p>test 4</p>
        <h2 id="s4-1">Head 4-1</h2><p>test 4-1</p>
        <h3 id="s4-2">Head 4-1-1</h3><p>test 4-1-1</p>
        <h1 id="s4-next">Head</h1><p>test next</p>
    """
    expected = """
                                   <p>test 4-1</p>
        <h3 id="s4-2">Head 4-1-1</h3><p>test 4-1-1</p>
    """  # h2 contents without the h2
    result = (parse(doc_src).extractSection(id="s4-1", ignore_heading=True)
                            .serialize())
    assert normalize_html(result) == normalize_html(expected)


class ReplaceSectionTests(TestCase):
    def test_basic_section_replace(self):
        doc_src = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        replace_src = """
            <h1 id="s2">Head 2</h1>
            <p>replacement worked</p>
        """
        expected = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s2">Head 2</h1>
            <p>replacement worked</p>
            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .replaceSection(id="s2", replace_src=replace_src)
                  .serialize())
        assert normalize_html(expected) == normalize_html(result)

    def test_ignore_heading_section_replace(self):
        doc_src = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        replace_src = """
            <p>replacement worked yay hooray</p>
        """
        expected = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s2">Head 2</h1>
            <p>replacement worked yay hooray</p>
            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .replaceSection(id="s2",
                                  replace_src=replace_src,
                                  ignore_heading=True)
                  .serialize())
        assert normalize_html(expected) == normalize_html(result)


class RemoveSectionTests(TestCase):
    def test_basic_section_remove(self):
        doc_src = """
            <h1 id="s1">Head 1</h1>
            <div id="here">Remove <span>this</span>.</div>
            <p>test</p>
            <div class="here">Leave <span>this</span>.</div>
        """
        expected = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <div class="here">Leave <span>this</span>.</div>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .removeSection('here')
                  .serialize())
        assert normalize_html(expected) == normalize_html(result)


class InjectSectionEditingLinksTests(TestCase):
    def test_section_edit_links(self):
        doc_src = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h2 id="s2">Head 2</h2>
            <p>test</p>
            <p>test</p>
            <h3 id="s3">Head 3</h3>
            <p>test</p>
            <p>test</p>
        """
        expected = """
            <h1 id="s1"><a class="edit-section" data-section-id="s1" data-section-src-url="/en-US/docs/some-slug?raw=true&amp;section=s1" href="/en-US/docs/some-slug$edit?edit_links=true&amp;section=s1" title="Edit section">Edit</a>Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h2 id="s2"><a class="edit-section" data-section-id="s2" data-section-src-url="/en-US/docs/some-slug?raw=true&amp;section=s2" href="/en-US/docs/some-slug$edit?edit_links=true&amp;section=s2" title="Edit section">Edit</a>Head 2</h2>
            <p>test</p>
            <p>test</p>
            <h3 id="s3"><a class="edit-section" data-section-id="s3" data-section-src-url="/en-US/docs/some-slug?raw=true&amp;section=s3" href="/en-US/docs/some-slug$edit?edit_links=true&amp;section=s3" title="Edit section">Edit</a>Head 3</h3>
            <p>test</p>
            <p>test</p>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .injectSectionEditingLinks('some-slug', 'en-US')
                  .serialize())
        assert normalize_html(expected) == normalize_html(result)


class CodeSyntaxFilterTests(TestCase):
    def test_code_syntax_conversion(self):
        doc_src = """
            <h2>Some JavaScript</h2>:
            <pre class="deki-transform" function="syntax.JavaScript">
            function foo(){
                alert("bar");
            }
            </pre>
            <pre>Some CSS:</pre>
            <pre class="dek-trans" function="syntax.CSS">
            .dek-trans { color: red; }
            </pre>
        """
        expected = """
            <h2>Some JavaScript</h2>:
            <pre class="brush: js">
            function foo(){
                alert("bar");
            }
            </pre>
            <pre>Some CSS:</pre>
            <pre class="brush: css">
            .dek-trans { color: red; }
            </pre>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .filter(CodeSyntaxFilter).serialize())
        assert normalize_html(expected) == normalize_html(result)


class SectionIDFilterTests(TestCase):
    def test_non_ascii_section_headers(self):
        headers = [
            (u'Documentation à propos de HTML',
             u'Documentation_à_propos_de_HTML'),
            (u'Outils facilitant le développement HTML',
             u'Outils_facilitant_le_développement_HTML'),
            (u'字面值(literals)',
             u'字面值(literals)'),
            (u'Documentação',
             u'Documentação'),
            (u'Lektury uzupełniające',
             u'Lektury_uzupełniające'),
            (u'Атрибуты',
             u'Атрибуты'),
            (u'HTML5 엘리먼트',
             u'HTML5_엘리먼트'),
            (u'Non safe title "#$%&+,/:;=?@[\\]^`{|}~',
             u'Non_safe_title'),
            (u"Five o'clock",
             u'Five_oclock'),
        ]

        section_filter = SectionIDFilter('')

        for original, slugified in headers:
            assert slugified == section_filter.slugify(original)


@pytest.mark.toc
class TOCFilterTests(TestCase):
    def test_generate_toc(self):
        doc_src = """
            <h2 id="HTML">HTML</h2>
              <h3 id="HTML5_canvas_element">HTML5 <code>canvas</code> element</h3>
            <h2 id="JavaScript">JavaScript</h2>
              JavaScript is awesome.
              <h3 id="WebGL">WebGL</h3>
              <h3 id="Audio">Audio</h3>
                <h4 id="Audio-API">Audio API</h4>
            <h2 id="CSS">CSS</h2>
                <h4 id="CSS_transforms">CSS transforms</h4>
              <h3 id="Gradients">Gradients</h3>
                <h4 id="Scaling_backgrounds">Scaling backgrounds</h4>
        """
        expected = """
            <li><a rel="internal" href="#HTML">HTML</a>
                <ol>
                  <li><a rel="internal" href="#HTML5_canvas_element">HTML5 <code>canvas</code> element</a></li>
                </ol>
            </li>
            <li><a rel="internal" href="#JavaScript">JavaScript</a>
                <ol>
                  <li><a rel="internal" href="#WebGL">WebGL</a>
                  <li><a rel="internal" href="#Audio">Audio</a>
                    <ol>
                      <li><a rel="internal" href="#Audio-API">Audio API</a></li>
                    </ol>
                  </li>
                </ol>
            </li>
            <li><a rel="internal" href="#CSS">CSS</a>
                <ol>
                  <li>
                    <ol>
                      <li><a rel="internal" href="#CSS_transforms">CSS transforms</a>
                    </ol>
                  </li>
                  <li><a rel="internal" href="#Gradients">Gradients</a>
                    <ol>
                      <li><a rel="internal" href="#Scaling_backgrounds">Scaling backgrounds</a>
                    </ol>
                </ol>
            </li>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .filter(SectionTOCFilter).serialize())
        assert normalize_html(expected) == normalize_html(result)

    def test_generate_toc_h2(self):
        doc_src = """
            <h2 id="HTML">HTML</h2>
              <h3 id="HTML5_canvas_element">HTML5 <code>canvas</code> element</h3>
            <h2 id="JavaScript">JavaScript</h2>
              JavaScript is awesome.
              <h3 id="WebGL">WebGL</h3>
              <h3 id="Audio">Audio</h3>
                <h4 id="Audio-API">Audio API</h4>
            <h2 id="CSS">CSS</h2>
                <h4 id="CSS_transforms">CSS transforms</h4>
              <h3 id="Gradients">Gradients</h3>
                <h4 id="Scaling_backgrounds">Scaling backgrounds</h4>
        """
        expected = """
            <li><a rel="internal" href="#HTML">HTML</a>
            </li>
            <li><a rel="internal" href="#JavaScript">JavaScript</a>
            </li>
            <li><a rel="internal" href="#CSS">CSS</a>
            </li>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .filter(H2TOCFilter).serialize())
        assert normalize_html(expected) == normalize_html(result)

    def test_generate_toc_h3(self):
        doc_src = """
            <h2 id="HTML">HTML</h2>
              <h3 id="HTML5_canvas_element">HTML5 <code>canvas</code> element</h3>
            <h2 id="JavaScript">JavaScript</h2>
              JavaScript is awesome.
              <h3 id="WebGL">WebGL</h3>
              <h3 id="Audio">Audio</h3>
                <h4 id="Audio-API">Audio API</h4>
            <h2 id="CSS">CSS</h2>
                <h4 id="CSS_transforms">CSS transforms</h4>
              <h3 id="Gradients">Gradients</h3>
                <h4 id="Scaling_backgrounds">Scaling backgrounds</h4>
        """
        expected = """
            <li><a rel="internal" href="#HTML">HTML</a>
                <ol>
                  <li><a rel="internal" href="#HTML5_canvas_element">HTML5 <code>canvas</code> element</a></li>
                </ol>
            </li>
            <li><a rel="internal" href="#JavaScript">JavaScript</a>
                <ol>
                  <li><a rel="internal" href="#WebGL">WebGL</a>
                  <li><a rel="internal" href="#Audio">Audio</a>
                  </li>
                </ol>
            </li>
            <li><a rel="internal" href="#CSS">CSS</a>
                <ol>
                  <li><a rel="internal" href="#Gradients">Gradients</a>
                </ol>
            </li>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .filter(H3TOCFilter).serialize())
        assert normalize_html(expected) == normalize_html(result)

    def test_bug_925043(self):
        '''Bug 925043 - Redesign TOC has a bunch of empty <code> tags in markup'''
        doc_src = """
            <h2 id="Print">Mastering <code>print</code></h2>
            <code>print 'Hello World!'</code>
        """
        expected = """
            <li>
                <a href="#Print" rel="internal">Mastering<code>print</code></a>
            </li>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .filter(SectionTOCFilter).serialize())
        assert normalize_html(expected) == normalize_html(result)


class FilterOutNoIncludeTests(TestCase):
    def test_noinclude(self):
        doc_src = u"""
            <div class="noinclude">{{ XULRefAttr() }}</div>
            <dl>
              <dt>{{ XULAttr(&quot;maxlength&quot;) }}</dt>
              <dd>Type: <em>integer</em></dd>
              <dd>Przykłady 例 예제 示例</dd>
            </dl>
            <div class="noinclude">
              <p>{{ languages( { &quot;ja&quot;: &quot;ja/XUL/Attribute/maxlength&quot; } ) }}</p>
            </div>
        """
        expected = u"""
            <dl>
              <dt>{{ XULAttr(&quot;maxlength&quot;) }}</dt>
              <dd>Type: <em>integer</em></dd>
              <dd>Przykłady 例 예제 示例</dd>
            </dl>
        """
        result = (kuma.wiki.content.filter_out_noinclude(doc_src))
        assert normalize_html(expected) == normalize_html(result)

    def test_noinclude_empty_content(self):
        """Bug 777475: The noinclude filter and pyquery seems to really dislike
        empty string as input"""
        doc_src = ''
        result = kuma.wiki.content.filter_out_noinclude(doc_src)
        assert result == ''


class BugizeTests(TestCase):
    def test_bugize_text(self):
        bad = 'Fixing bug #12345 again. <img src="http://davidwalsh.name" /> <a href="">javascript></a>'
        good = 'Fixing <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345" target="_blank" rel="noopener">bug 12345</a> again. &lt;img src=&#34;http://davidwalsh.name&#34; /&gt; &lt;a href=&#34;&#34;&gt;javascript&gt;&lt;/a&gt;'
        assert bugize_text(bad) == Markup(good)

        bad_upper = 'Fixing Bug #12345 again.'
        good_upper = 'Fixing <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345" target="_blank" rel="noopener">Bug 12345</a> again.'
        assert bugize_text(bad_upper) == Markup(good_upper)


def test_filteriframe():
    """The filter drops iframe src that does not match the pattern."""
    slug = 'test-code-embed'
    embed_url = 'https://sampleserver/en-US/docs/%s$samples/sample1' % slug
    doc_src = """\
        <p>This is a page. Deal with it.</p>
        <iframe id="if1" src="%(embed_url)s"></iframe>
        <iframe id="if2" src="https://testserver"></iframe>
        <iframe id="if3" src="https://some.alien.site.com"></iframe>
        <iframe id="if4" src="http://davidwalsh.name"></iframe>
        <iframe id="if5" src="ftp://davidwalsh.name"></iframe>
        <p>test</p>
        """ % dict(embed_url=embed_url)

    patterns = [
        ('https', 'sampleserver', ''),
        ('https', 'testserver', ''),
    ]
    result_src = parse(doc_src).filterIframeHosts(patterns).serialize()
    page = pq(result_src)
    assert page('#if1').attr('src') == embed_url
    assert page('#if2').attr('src') == 'https://testserver'
    assert page('#if3').attr('src') == ''
    assert page('#if4').attr('src') == ''
    assert page('#if5').attr('src') == ''


def test_filteriframe_empty_contents():
    """Any contents inside an <iframe> should be removed."""
    doc_src = """
        <iframe>
        <iframe src="javascript:alert(1);"></iframe>
        </iframe>
    """
    expected_src = """
        <iframe>
        </iframe>
    """
    patterns = [('https', 'sampleserver', '')]
    result_src = parse(doc_src).filterIframeHosts(patterns).serialize()
    assert normalize_html(expected_src) == normalize_html(result_src)


FILTERIFRAME_ACCEPTED = {
    'youtube_ssl': ('https://www.youtube.com/embed/'
                    'iaNoBlae5Qw/?feature=player_detailpage'),
    'prod': ('https://mdn.mozillademos.org/'
             'en-US/docs/Web/CSS/text-align$samples/alignment?revision=456'),
    'newrelic': 'https://rpm.newrelic.com/public/charts/9PqtkrTkoo5',
    'jsfiddle': 'https://jsfiddle.net/78dg25ax/embedded/js,result/',
    'github.io': ('https://mdn.github.io/webgl-examples/'
                  'tutorial/sample6/index.html'),
    'ie_moz_net': ('https://interactive-examples.mdn.mozilla.net/'
                   'pages/js/array-push.html'),
    'code_sample': (settings.PROTOCOL + settings.ATTACHMENT_HOST +
                    '/de/docs/Test$samples/test?revision=678'),
    'interactive': (settings.INTERACTIVE_EXAMPLES_BASE +
                    '/pages/http/headers.html')
}

FILTERIFRAME_REJECTED = {
    'alien': 'https://some.alien.site.com',
    'dwalsh_web': 'http://davidwalsh.name',
    'dwalsh_ftp': 'ftp://davidwalsh.name',
    'js': 'javascript:alert(1);',
    'youtube_other': 'https://youtube.com/sembed/',
    'prod_old': ('https://mozillademos.org/'
                 'en-US/docs/Web/CSS/text-align$samples/alignment?revision=456'),
    'vagrant': ('https://developer-local.allizom.org/'
                'en-US/docs/Test$samples/sample1?revision=123'),
    'vagrant_2': ('http://developer-local:81/'
                  'en-US/docs/Test$samples/sample1?revision=123'),
    'cdn': ('https://developer.cdn.mozilla.net/is/this/valid?'),
    'stage': ('https://stage-files.mdn.moz.works/'
              'fr/docs/Test$samples/sample2?revision=234'),
    'test': 'http://testserver/en-US/docs/Test$samples/test?revision=567',
    'youtube_no_www': ('https://youtube.com/embed/'
                       'iaNoBlae5Qw/?feature=player_detailpage'),
    'youtube_http': ('http://www.youtube.com/embed/'
                     'iaNoBlae5Qw/?feature=player_detailpage'),
    'youtube_other2': 'https://www.youtube.com/sembed/',
    'jsfiddle_other': 'https://jsfiddle.net/about',
}


@pytest.mark.parametrize('url', list(FILTERIFRAME_ACCEPTED.values()),
                         ids=list(FILTERIFRAME_ACCEPTED))
def test_filteriframe_default_accepted(url, settings):
    doc_src = '<iframe id="test" src="%s"></iframe>' % url
    patterns = settings.ALLOWED_IFRAME_PATTERNS
    result_src = parse(doc_src).filterIframeHosts(patterns).serialize()
    page = pq(result_src)
    assert page('#test').attr('src') == url


@pytest.mark.parametrize('url', list(FILTERIFRAME_REJECTED.values()),
                         ids=list(FILTERIFRAME_REJECTED))
def test_filteriframe_default_rejected(url, settings):
    doc_src = '<iframe id="test" src="%s"></iframe>' % url
    patterns = settings.ALLOWED_IFRAME_PATTERNS
    result_src = parse(doc_src).filterIframeHosts(patterns).serialize()
    page = pq(result_src)
    assert page('#test').attr('src') == ''


BLEACH_INVALID_HREFS = {
    'b64_script1': ('data:text/html;base64,' +
                    b64encode(b'<script>alert("document.cookie:" + document.cookie);').decode('utf-8')),
    'b64_script2': ('data:text/html;base64,' +
                    b64encode(b'<script>alert(document.domain)</script>').decode('utf-8')),
    'javascript': 'javascript:alert(1)',
    'js_htmlref1': 'javas&#x09;cript:alert(1)',
    'js_htmlref2': '&#14;javascript:alert(1)',
}

BLEACH_VALID_HREFS = {
    'relative': '/docs/ok/test',
    'http': 'http://example.com/docs/ok/test',
    'https': 'https://example.com/docs/ok/test',
}


@pytest.mark.parametrize('href', list(BLEACH_INVALID_HREFS.values()),
                         ids=list(BLEACH_INVALID_HREFS))
def test_bleach_clean_removes_invalid_hrefs(href):
    """Bleach removes invalid hrefs."""
    html = '<p><a id="test" href="%s">click me</a></p>' % href
    result = bleach.clean(html,
                          tags=ALLOWED_TAGS,
                          attributes=ALLOWED_ATTRIBUTES,
                          protocols=ALLOWED_PROTOCOLS)
    link = pq(result).find('#test')
    assert link.attr('href') is None


@pytest.mark.parametrize('href', list(BLEACH_VALID_HREFS.values()),
                         ids=list(BLEACH_VALID_HREFS))
def test_bleach_clean_hrefs(href):
    """Bleach retains valid hrefs."""
    html = '<p><a id="test" href="%s">click me</a></p>' % href
    result = bleach.clean(html,
                          tags=ALLOWED_TAGS,
                          attributes=ALLOWED_ATTRIBUTES,
                          protocols=ALLOWED_PROTOCOLS)
    link = pq(result).find('#test')
    assert link.attr('href') == href


def test_annotate_links_encoded_utf8(db):
    """Encoded UTF8 characters in links are decoded."""
    Document.objects.create(locale='fr', slug=u'CSS/Héritage',
                            title=u'Héritée')
    html = normalize_html(
        u'<li><a href="/fr/docs/CSS/H%c3%a9ritage">Héritée</a></li>')
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


@pytest.mark.parametrize('has_class', ('hasClass', 'noClass'))
@pytest.mark.parametrize('anchor', ('withAnchor', 'noAnchor'))
@pytest.mark.parametrize('full_url', ('fullURL', 'pathOnly'))
def test_annotate_links_existing_doc(root_doc, anchor, full_url, has_class):
    """Links to existing docs are unmodified."""
    if full_url == 'fullURL':
        url = root_doc.get_full_url()
        assert url.startswith(settings.SITE_URL)
    else:
        url = root_doc.get_absolute_url()
    if anchor == 'withAnchor':
        url += "#anchor"
    if has_class == 'hasClass':
        link_class = ' class="extra"'
    else:
        link_class = ''
    html = normalize_html('<li><a %s href="%s"></li>' % (link_class, url))
    actual_raw = normalize_html(
        parse(html).annotateLinks(base_url=settings.SITE_URL).serialize())
    assert actual_raw == html


@pytest.mark.parametrize('has_class', ('hasClass', 'noClass'))
@pytest.mark.parametrize('anchor', ('withAnchor', 'noAnchor'))
@pytest.mark.parametrize('full_url', ('fullURL', 'pathOnly'))
def test_annotate_links_nonexisting_doc(db, anchor, full_url, has_class):
    """Links to missing docs get extra attributes."""
    url = 'en-US/docs/Root'
    if full_url == 'fullURL':
        url = urljoin(AL_BASE_URL, url)
    if anchor == 'withAnchor':
        url += "#anchor"
    if has_class == 'hasClass':
        link_class = ' class="extra"'
        expected_attrs = ' class="extra new" rel="nofollow"'
    else:
        link_class = ''
        expected_attrs = ' class="new" rel="nofollow"'
    html = '<li><a %s href="%s"></li>' % (link_class, url)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    expected_raw = '<li><a %s href="%s"></li>' % (expected_attrs, url)
    assert normalize_html(actual_raw) == normalize_html(expected_raw)


def test_annotate_links_uilocale_to_existing_doc(root_doc):
    """Links to existing docs with embeded locales are unmodified."""
    assert root_doc.get_absolute_url() == '/en-US/docs/Root'
    url = '/en-US/docs/en-US/Root'  # Notice the 'en-US' after '/docs/'
    html = normalize_html('<li><a href="%s"></li>' % url)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


def test_annotate_links_uilocale_to_nonexisting_doc(db):
    """Links to new docs with embeded locales are modified."""
    url = '/en-US/docs/en-US/Root'  # Notice the 'en-US' after '/docs/'
    html = '<li><a href="%s"></li>' % url
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    expected = normalize_html(
        '<li><a rel="nofollow" class="new" href="%s"></li>' % url)
    assert normalize_html(actual_raw) == expected


@pytest.mark.parametrize('attributes', ('', 'class="foobar" name="quux"'))
def test_annotate_links_no_href(attributes):
    """Links without an href do not break the annotator."""
    html = normalize_html('<li><a %s>No href</a></li>' % attributes)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


@pytest.mark.parametrize('slug', ('tag/foo', 'feeds/atom/all', 'templates'))
def test_annotate_links_docs_but_not_wiki_urls(slug):
    """Links to /docs/ URLs that are not wiki docs are not annotated."""
    html = normalize_html('<li><a href="/en-US/docs/%s">Other</a></li>' % slug)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


@pytest.mark.parametrize('slug', ('', '/dashboards/revisions'))
def test_annotate_links_not_docs_urls(slug):
    """Links that are not /docs/ are not annotated."""
    html = normalize_html('<li><a href="%s">Other</a></li>' % slug)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


@pytest.mark.parametrize('slug', ('root', 'ROOT', 'rOoT'))
def test_annotate_links_case_insensitive(root_doc, slug):
    """Links to existing docs are case insensitive."""
    url = '/en-US/docs/' + slug
    assert url != root_doc.get_absolute_url()
    html = normalize_html('<li><a href="%s"></li>' % url)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


def test_annotate_links_collation_insensitive(db):
    """Links to existing docs are collation-insensitive.

    Under MySQL's utf8_general_ci collation, é == e
    """
    accent = u'Récursion'
    no_accent = u'Recursion'
    assert accent.lower() != no_accent.lower
    Document.objects.create(locale='fr', slug=u'Glossaire/' + accent,
                            title=accent)
    html = normalize_html(
        u'<li><a href="/fr/docs/Absent"></li>' +
        u'<li><a href="/fr/docs/Glossaire/%s"></li>' % no_accent)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    expected = normalize_html(
        u'<li><a class="new" rel="nofollow" href="/fr/docs/Absent"></li>' +
        u'<li><a href="/fr/docs/Glossaire/%s"></li>' % no_accent)
    assert normalize_html(actual_raw) == expected


def test_annotate_links_external_link():
    """Links to external sites get an external class."""
    html = '<li><a href="https://mozilla.org">External link</a>.</li>'
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    expected = normalize_html(
        '<li><a class="external" rel="noopener" href="https://mozilla.org">'
        'External link</a>.</li>')
    assert normalize_html(actual_raw) == expected


class FilterEditorSafetyTests(TestCase):
    def test_editor_safety_filter(self):
        """Markup that's hazardous for editing should be stripped"""
        doc_src = """
            <svg><circle onload=confirm(3)>
            <h1 class="header1">Header One</h1>
            <p>test</p>
            <section onclick="alert('hacked!')">
                <h1 class="header2">Header Two</h1>
                <p>test</p>
            </section>
            <h1 class="header3">Header Three</h1>
            <p>test</p>
        """
        expected_src = """
            <svg><circle>
            <h1 class="header1">Header One</h1>
            <p>test</p>
            <section>
                <h1 class="header2">Header Two</h1>
                <p>test</p>
            </section>
            <h1 class="header3">Header Three</h1>
            <p>test</p>
        """
        result_src = (kuma.wiki.content.parse(doc_src)
                      .filterEditorSafety()
                      .serialize())
        assert normalize_html(expected_src) == normalize_html(result_src)


@pytest.mark.parametrize(
    'tag',
    # Sample of tags from ALLOWED_TAGS
    ('address',
     'article',
     'code',
     'datagrid',
     'details',
     'dt',
     'figure',
     'h5',
     'mark',
     'output',
     'pre',
     'progress',
     ))
def test_clean_content_allows_simple_tag(tag):
    """clean_content allows simple tags, id attribute."""
    html = '<{tag} id="{id}"></{tag}>'.format(
        tag=tag, id='sect1' if tag == 'h5' else 'foo')
    assert clean_content(html) == html


@pytest.mark.parametrize(
    'tag',
    ('br',
     'command',
     'img',
     'input',
     ))
def test_clean_content_allows_self_closed_tags(tag):
    """clean_content allows self-closed tags."""
    html = '<%s>' % tag
    assert clean_content(html) == html


def test_clean_content_preserves_whitespace():
    """clean_content allows an HTML table."""
    html = ('<table><thead><tr><th>foo</th></tr></thead>'
            '<tbody><tr><td>foo</td></tr></tbody></table>')
    assert clean_content(html) == html


@pytest.mark.parametrize(
    'html,expected',
    (('<command  id="foo">',
      '<command id="foo">'),
     (('<img class="foo"  title="foo" src="foo" align="left" '
       'alt="picture of foo"  dir="rtl" id="foo">'),
      ('<img align="left" alt="picture of foo" class="foo" dir="rtl" id="foo" '
       'src="foo" title="foo">')),
     ('<a href="foo" title="foo" id="foo"  class="foo">foo</a>',
      '<a class="foo" href="foo" id="foo" title="foo">foo</a>'),
     ('<div class="foo" >foo</div>',
      '<div class="foo">foo</div>'),
     (('<video  id="some-movie" src="some-movie.mpg" class="movie" '
       'controls lang="en-US">Fallback</video>'),
      ('<video class="movie" controls id="some-movie" lang="en-US" '
       'src="some-movie.mpg">Fallback</video>')),
     ))
def test_clean_content_allows_some_attributes(html, expected):
    """
    clean_content allows attributes, orders them alphabetically, and
    normalizes whitespace between them.
    """
    assert clean_content(html) == expected


def test_clean_content_allows_some_styles():
    """clean_content allows some style values."""
    html = '<span style="font-size: 24px; rotate: 90deg"></span>'
    assert clean_content(html) == '<span style="font-size: 24px;"></span>'


def test_clean_content_stripped_ie_comment():
    """bug 801046: strip IE conditional comments"""
    content = """
        <p>Hi there.</p>
        <!--[if]><script>alert(1)</script -->
        <!--[if<img src=x onerror=alert(2)//]> -->
        <p>Goodbye</p>
    """
    expected = """
        <p>Hi there.</p>
        <p>Goodbye</p>
    """
    result = clean_content(content)
    assert normalize_html(expected) == normalize_html(result)


def test_clean_content_iframe_in_script():
    """iframe in script should be filtered"""
    content = ('<script><iframe src="data:text/plain,foo">'
               '</iframe></script>')
    expected = ('&lt;script&gt;&lt;iframe src="data:text/plain,foo"&gt;'
                '&lt;/iframe&gt;&lt;/script&gt;')
    result = clean_content(content)
    assert normalize_html(expected) == normalize_html(result)


def test_clean_content_iframe_in_style():
    """iframe in style should be filtered"""
    content = ('<style><iframe src="data:text/plain,foo">'
               '</iframe></style>')
    expected = ('&lt;style&gt;&lt;iframe src="data:text/plain,foo"&gt;'
                '&lt;/iframe&gt;&lt;/style&gt;')
    result = clean_content(content)
    assert normalize_html(expected) == normalize_html(result)


def test_clean_content_iframe_in_textarea():
    """
    iframe in textarea should not be filtered since it's not parsed as tag
    """
    content = """
        <textarea><iframe src="data:text/plain,foo"></iframe></textarea>
    """
    expected = """
        <textarea><iframe src="data:text/plain,foo"></iframe></textarea>
    """
    result = clean_content(content)
    assert normalize_html(expected) == normalize_html(result)


def test_clean_content_filter_iframe(settings):
    """iframe src is filtered by default."""
    settings.ALLOW_ALL_IFRAMES = False
    html = '<iframe src="http://hacks.example.com"></iframe>'
    assert clean_content(html) == '<iframe src=""></iframe>'


def test_clean_content_allow_all_iframes(settings):
    """iframe src is filtered by default."""
    settings.ALLOW_ALL_IFRAMES = True
    html = '<iframe src="http://hacks.example.com"></iframe>'
    assert clean_content(html) == html


def test_clean_removes_empty_paragraphs():
    """bug 1553512: fix the insertion of blank paragraphs when pasting text"""
    content = """
        <p>Hi there.</p>
        <p></p>
        <p>Goodbye</p>
        </p>
    """
    expected = """
        <p>Hi there.</p>
        <p>Goodbye</p>
    """
    result = clean_content(content)
    assert normalize_html(expected) == normalize_html(result)


def test_extractor_css_classnames(root_doc, wiki_user):
    """The Extractor can return the CSS class names in use."""
    classes = ('foobar', 'barfoo', 'bazquux')
    content = """
        <p class="%s">Test</p>
        <p class="%s">Test</p>
        <div class="%s">Test</div>
        <div>No Class</div>
    """ % classes
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    root_doc.render()  # Also saves
    result = root_doc.extract.css_classnames()
    assert sorted(result) == sorted(classes)


def test_extractor_html_attributes(root_doc, wiki_user):
    """The Extractor can return the HTML attributes."""
    attributes = (
        'class="foobar"',
        'id="frazzy"',
        'lang="farb"',
    )
    content = """
        <p %s>Test</p>
        <p %s>Test</p>
        <div %s>Test</div>
    """ % attributes
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    root_doc.render()  # Also saves
    result = root_doc.extract.html_attributes()
    assert sorted(result) == sorted(attributes)


def test_extractor_macro_names(root_doc, wiki_user):
    """The Extractor can return the names of KumaScript macros."""
    macros = ('foobar', 'barfoo', 'bazquux', 'banana')
    content = """
        <p>{{ %s }}</p>
        <p>{{ %s("foo", "bar", "baz") }}</p>
        <p>{{ %s    ("quux") }}</p>
        <p>{{%s}}</p>
    """ % macros
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    result = root_doc.extract.macro_names()
    assert sorted(result) == sorted(macros)


@pytest.mark.parametrize('is_rendered', (True, False))
@pytest.mark.parametrize('method', ('macro_names', 'css_classnames',
                                    'html_attributes'))
def test_extractor_no_content(method, is_rendered, root_doc, wiki_user):
    """The Extractor returns empty lists when the document has no content."""
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content='', creator=wiki_user)
    if is_rendered:
        root_doc.render()
    result = getattr(root_doc.extract, method)()
    assert result == []


def test_extractor_code_sample(root_doc, wiki_user):
    """The Extractor can return the sections of a code sample."""
    code_sample = {
        'html': 'Some HTML',
        'css': '.some-css { color: red; }',
        'js': 'window.alert("HI THERE")',
    }
    content = """
        <div id="sample" class="code-sample">
            <pre class="brush: html">%(html)s</pre>
            <pre class="brush: css">%(css)s</pre>
            <pre class="brush: js">%(js)s</pre>
        </div>
        {{ EmbedLiveSample('sample1') }}
    """ % code_sample
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    result = root_doc.extract.code_sample('sample')
    assert result == code_sample


def test_extractor_code_sample_unescape(root_doc, wiki_user):
    '''The Extractor unescapes content in <pre> blocks.'''
    sample_html = u"""
        <div class="foo">
            <p>Hello world!</p>
            <p>Unicode fun: Przykłady 例 예제 示例</p>
        </div>
    """
    sample_css = ".foo p:before { content: '> '; }"
    sample_js = 'window.alert("Hi there!");'
    assert sample_html != escape(sample_html)
    assert sample_css != escape(sample_css)
    assert sample_js != escape(sample_js)
    content = """
        <h3>Sample Code Section Heade</h3>
        <ul id="sample" class="code-sample">
            <li><span>HTML</span>
                <pre class="brush: html">%s</pre>
            </li>
            <li><span>CSS</span>
                <pre class="brush:css;random:crap;in:the;classname">%s</pre>
            </li>
            <li><span>JS</span>
                <pre class="brush: js">%s</pre>
            </li>
        </ul>
    """ % (escape(sample_html), escape(sample_css), escape(sample_js))
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    result = root_doc.extract.code_sample('sample')
    assert sample_html.strip() == result['html'].strip()
    assert sample_css == result['css']
    assert sample_js == result['js']


def test_extractor_code_sample_nbsp_is_converted(root_doc, wiki_user):
    """
    Non-breaking spaces are turned to normal spaces in code sample
    extraction.

    Reported in bug 819999 and 1284781
    """
    content = """
        <h2 id="With_nbsp">With &amp;nbsp;</h2>
        <pre class="brush: css">
        .widget select,
        .no-widget .select {
        &nbsp; position : absolute;
        &nbsp; left&nbsp;&nbsp;&nbsp;&nbsp; : -5000em;
        &nbsp; height&nbsp;&nbsp; : 0;
        &nbsp; overflow : hidden;
        }
        </pre>
    """
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    result = root_doc.extract.code_sample('With_nbsp')
    assert u'\xa0' not in result['css']
    assert '&nbsp;' not in result['css']


@pytest.mark.parametrize('skip_part', ('html', 'css', 'js', 'all'))
def test_extractor_code_sample_missing_parts(root_doc, wiki_user, skip_part):
    """The Extractor returns None if a code sample section is missing."""
    parts = {}
    expected = {}
    for part in ('html', 'css', 'js'):
        if skip_part in (part, 'all'):
            parts[part] = ''
            expected[part] = None
        else:
            parts[part] = '<pre class="brush: %s">included</pre>' % part
            expected[part] = 'included'
    content = """
    <h3 id='Code_Sample'>Code Sample</h3>
    %(html)s
    %(css)s
    %(js)s
    """ % parts

    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    result = root_doc.extract.code_sample('Code_Sample')
    assert result == expected


@pytest.mark.parametrize('sample_id', ('Bug:1173170',       # bug 1173170
                                       u'sam\x00ple',       # bug 1269143
                                       u"""sam<'&">ple""",  # bug 1269143
                                       ))
def test_extractor_code_sample_with_problem_id(root_doc, wiki_user, sample_id):
    """The Extractor does not error if the code sample ID is bad."""
    content = """
        <div id="sample" class="code-sample">
            <pre class="brush: html">Some HTML</pre>
            <pre class="brush: css">.some-css { color: red; }</pre>
            <pre class="brush: js">window.alert("HI THERE")</pre>
        </div>
        {{ EmbedLiveSample('sample1') }}
    """
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=content, creator=wiki_user)
    result = root_doc.extract.code_sample(sample_id)
    assert result == {'html': None, 'css': None, 'js': None}


@pytest.mark.parametrize('annotate_links', [True, False])
def test_extractor_section(root_doc, annotate_links):
    """The Extractor can extract a section, optionally annotating links."""
    quick_links_template = """
    <ul>
      <li><a href="/en-US/docs/Root">Existing</a></li>
      <li><a %s href="/en-US/docs/New">New</a></li>
    </ul>
    """
    quick_links = quick_links_template % ''
    if annotate_links:
        expected = quick_links_template % 'rel="nofollow" class="new"'
    else:
        expected = quick_links
    content = """
        <div>
          <section id="Quick_Links" class="Quick_Links">
            %s
          </section>
        </div>
    """ % quick_links
    result = root_doc.extract.section(content, "Quick_Links",
                                      annotate_links=annotate_links)
    assert normalize_html(result) == normalize_html(expected)


@pytest.mark.parametrize('wrapper', list(SUMMARY_PLUS_SEO_WRAPPERS.values()),
                         ids=list(SUMMARY_PLUS_SEO_WRAPPERS))
@pytest.mark.parametrize('markup, text', list(SUMMARY_CONTENT.values()),
                         ids=list(SUMMARY_CONTENT))
def test_summary_section(markup, text, wrapper):
    content = wrapper.format(markup)
    assert get_seo_description(content, 'en-US') == text
    assert normalize_html(get_seo_description(content, 'en-US', False)) == normalize_html(markup)


@pytest.mark.parametrize('wrapper', list(SUMMARY_WRAPPERS.values()),
                         ids=list(SUMMARY_WRAPPERS))
@pytest.mark.parametrize('markup, expected_markup, text',
                         list(SUMMARIES_SEO_CONTENT.values()),
                         ids=list(SUMMARIES_SEO_CONTENT))
def test_multiple_seo_summaries(markup, expected_markup, text, wrapper):
    content = wrapper.format(markup)
    assert get_seo_description(content, 'en-US') == text
    assert normalize_html(get_seo_description(content, 'en-US', False)) == normalize_html(expected_markup)


def test_empty_paragraph_content():
    content = u"""<p></p><div class="overheadIndicator draft draftHeader">
        <strong>DRAFT</strong>
        <div>This page is not complete.</div>
        </div><p></p>
        <p></p><div class="note"><strong>Note:</strong> Please do not
        translate this page until it is done; it will be much easier at
        that point. The French translation is a test to be sure that it
        works well.</div><p></p>"""
    assert get_seo_description(content, 'en-US', False) == ''


def test_content_is_a_url(mock_requests):
    # Note! the `mock_requests` fixture is just there to make absolutely
    # sure the whole test doesn't ever use requests.get().
    # My not setting up expectations, and if it got used,
    # these tests would raise a `NoMockAddress` exception.

    url = u'https://developer.mozilla.org'
    assert get_seo_description(url, 'en-US', False) == ''

    # Doesn't matter if it's http or https
    assert get_seo_description(url.replace('s:/', ':/'), 'en-US', False) == ''

    # If the content, afterwards, has real paragraphs, then the first
    # line becomes the seo description
    real_line = u'\n<p>This is the second line</p>'
    assert get_seo_description(url + real_line, 'en-US', False) == url
