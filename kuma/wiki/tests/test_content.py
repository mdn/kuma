# -*- coding: utf-8 -*-
from urlparse import urljoin

from django.conf import settings
from django.test import TestCase
from jinja2 import escape, Markup
from pyquery import PyQuery as pq
import bleach
import mock
import pytest

import kuma.wiki.content
from kuma.core.tests import KumaTestCase, eq_, ok_
from kuma.users.tests import UserTestCase

from . import document, normalize_html, revision

from ..constants import ALLOWED_ATTRIBUTES, ALLOWED_PROTOCOLS, ALLOWED_TAGS
from ..content import (SECTION_TAGS, CodeSyntaxFilter, H2TOCFilter,
                       H3TOCFilter, SectionIDFilter, SectionTOCFilter,
                       get_content_sections, get_seo_description, parse)
from ..models import Document
from ..templatetags.jinja_helpers import bugize_text

AL_BASE_URL = 'https://example.com'  # Base URL for annotateLinks tests


class GetContentSectionsTests(TestCase):
    def test_section_pars_for_empty_docs(self):
        doc = document(title='Doc', locale=u'fr', slug=u'doc', save=True,
                       html='<!-- -->')
        res = get_content_sections(doc.html)
        eq_(type(res).__name__, 'list')


class InjectSectionIDsTests(TestCase):
    def test_section_ids(self):

        doc_src = """
            <h1 class="header1">Header One</h1>
            <p>test</p>
            <section>
                <h1 class="header2">Header Two</h1>
                <p>test</p>
            </section>
            <h2 name="Constants" class="hasname">This title does not match the name</h2>
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
            ('hasname', 'Constants'),
            ('hasid', 'This_text_clobbers_the_ID'),
            ('Quick_Links', 'Quick_Links'),
        )
        for cls, id in expected:
            eq_(id, result_doc.find('.%s' % cls).attr('id'))

        # Then, ensure all elements in need of an ID now all have unique IDs.
        ok_(len(SECTION_TAGS) > 0)
        els = result_doc.find(', '.join(SECTION_TAGS))
        seen_ids = set()
        for i in range(0, len(els)):
            id = els.eq(i).attr('id')
            ok_(id is not None)
            ok_(id not in seen_ids)
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


class ExtractSectionTests(TestCase):
    def test_simple_implicit_section_extract(self):
        doc_src = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>
        """
        expected = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>
        """
        result = (kuma.wiki.content.parse(doc_src)
                                   .extractSection(id="s1")
                                   .serialize())
        eq_(normalize_html(expected), normalize_html(result))

    def test_contained_implicit_section_extract(self):
        doc_src = """
            <h1 id="s4-next">Head</h1>
            <p>test</p>

            <section id="parent-s5">
                <h1 id="s5">Head 5</h1>
                <p>test</p>
                <p>test</p>
                <section>
                    <h1>head subsection</h1>
                </section>
                <h2 id="s5-1">Head 5-1</h2>
                <p>test</p>
                <p>test</p>
                <h1 id="s5-next">Head 5 next</h1>
                <p>test</p>
                <p>test</p>
            </section>

            <h1 id="s7">Head 7</h1>
            <p>test</p>
            <p>test</p>
        """
        expected = """
                <h1 id="s5">Head 5</h1>
                <p>test</p>
                <p>test</p>
                <section>
                    <h1>head subsection</h1>
                </section>
                <h2 id="s5-1">Head 5-1</h2>
                <p>test</p>
                <p>test</p>
        """
        result = (kuma.wiki.content.parse(doc_src)
                                   .extractSection(id="s5")
                                   .serialize())
        eq_(normalize_html(expected), normalize_html(result))

    def test_explicit_section_extract(self):
        doc_src = """
            <h1 id="s4-next">Head</h1>
            <p>test</p>

            <section id="parent-s5">
                <h1 id="s5">Head 5</h1>
                <p>test</p>
                <p>test</p>
                <section>
                    <h1>head subsection</h1>
                </section>
                <h2 id="s5-1">Head 5-1</h2>
                <p>test</p>
                <p>test</p>
                <h1 id="s5-next">Head 5 next</h1>
                <p>test</p>
                <p>test</p>
            </section>

            <h1 id="s7">Head 7</h1>
            <p>test</p>
            <p>test</p>
        """
        expected = """
                <h1 id="s5">Head 5</h1>
                <p>test</p>
                <p>test</p>
                <section>
                    <h1>head subsection</h1>
                </section>
                <h2 id="s5-1">Head 5-1</h2>
                <p>test</p>
                <p>test</p>
                <h1 id="s5-next">Head 5 next</h1>
                <p>test</p>
                <p>test</p>
        """
        result = (kuma.wiki.content.parse(doc_src)
                                   .extractSection(id="parent-s5")
                                   .serialize())
        eq_(normalize_html(expected), normalize_html(result))

    def test_multilevel_implicit_section_extract(self):
        doc_src = """
            <p>test</p>

            <h1 id="s4">Head 4</h1>
            <p>test</p>
            <p>test</p>
            <h2 id="s4-1">Head 4-1</h2>
            <p>test</p>
            <p>test</p>
            <h3 id="s4-2">Head 4-1-1</h3>
            <p>test</p>
            <p>test</p>

            <h1 id="s4-next">Head</h1>
            <p>test</p>
        """
        expected = """
            <h1 id="s4">Head 4</h1>
            <p>test</p>
            <p>test</p>
            <h2 id="s4-1">Head 4-1</h1>
            <p>test</p>
            <p>test</p>
            <h3 id="s4-2">Head 4-1-1</h1>
            <p>test</p>
            <p>test</p>
        """
        result = (kuma.wiki.content.parse(doc_src)
                                   .extractSection(id="s4")
                                   .serialize())
        eq_(normalize_html(expected), normalize_html(result))

    def test_morelevels_implicit_section_extract(self):
        doc_src = """
            <h1 id="s7">Head 7</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s8">Head</h1>
            <p>test</p>
            <h2 id="s8-1">Head</h1>
            <p>test</p>
            <h3 id="s8-1-1">Head</h3>
            <p>test</p>
            <h2 id="s8-2">Head</h1>
            <p>test</p>
            <h3 id="s8-2-1">Head</h3>
            <p>test</p>
            <h4 id="s8-2-1-1">Head</h4>
            <p>test</p>
            <h2 id="s8-3">Head</h1>
            <p>test</p>

            <h1 id="s9">Head</h1>
            <p>test</p>
            <p>test</p>
        """
        expected = """
            <h1 id="s8">Head</h1>
            <p>test</p>
            <h2 id="s8-1">Head</h1>
            <p>test</p>
            <h3 id="s8-1-1">Head</h3>
            <p>test</p>
            <h2 id="s8-2">Head</h1>
            <p>test</p>
            <h3 id="s8-2-1">Head</h3>
            <p>test</p>
            <h4 id="s8-2-1-1">Head</h4>
            <p>test</p>
            <h2 id="s8-3">Head</h1>
            <p>test</p>
        """
        result = (kuma.wiki.content.parse(doc_src)
                                   .extractSection(id="s8")
                                   .serialize())
        eq_(normalize_html(expected), normalize_html(result))

    def test_ignore_heading_section_extract(self):
        doc_src = """
            <p>test</p>
            <h1 id="s4">Head 4</h1>
            <p>test</p>
            <h2 id="s4-1">Head 4-1</h2>
            <p>test</p>
            <h3 id="s4-2">Head 4-1-1</h3>
            <p>test s4-2</p>
            <h1 id="s4-next">Head</h1>
            <p>test</p>
        """
        expected = """
            <p>test</p>
            <h3 id="s4-2">Head 4-1-1</h3>
            <p>test s4-2</p>
        """
        result = (kuma.wiki.content.parse(doc_src)
                                   .extractSection(id="s4-1",
                                                   ignore_heading=True)
                                   .serialize())
        eq_(normalize_html(expected), normalize_html(result))


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
        eq_(normalize_html(expected), normalize_html(result))

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
        eq_(normalize_html(expected), normalize_html(result))


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
            <h1 id="s1"><a class="edit-section" data-section-id="s1" data-section-src-url="/en-US/docs/some-slug?raw=true&amp;section=s1" href="/en-US/docs/some-slug$edit?section=s1&amp;edit_links=true" title="Edit section">Edit</a>Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h2 id="s2"><a class="edit-section" data-section-id="s2" data-section-src-url="/en-US/docs/some-slug?raw=true&amp;section=s2" href="/en-US/docs/some-slug$edit?section=s2&amp;edit_links=true" title="Edit section">Edit</a>Head 2</h2>
            <p>test</p>
            <p>test</p>
            <h3 id="s3"><a class="edit-section" data-section-id="s3" data-section-src-url="/en-US/docs/some-slug?raw=true&amp;section=s3" href="/en-US/docs/some-slug$edit?section=s3&amp;edit_links=true" title="Edit section">Edit</a>Head 3</h3>
            <p>test</p>
            <p>test</p>
        """
        result = (kuma.wiki.content
                  .parse(doc_src)
                  .injectSectionEditingLinks('some-slug', 'en-US')
                  .serialize())
        eq_(normalize_html(expected), normalize_html(result))


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
        eq_(normalize_html(expected), normalize_html(result))


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
        ]

        section_filter = SectionIDFilter('')

        for original, slugified in headers:
            ok_(slugified == section_filter.slugify(original))


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
        eq_(normalize_html(expected), normalize_html(result))

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
        eq_(normalize_html(expected), normalize_html(result))

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
        eq_(normalize_html(expected), normalize_html(result))

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
        eq_(normalize_html(expected), normalize_html(result))


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
        eq_(normalize_html(expected), normalize_html(result))

    def test_noinclude_empty_content(self):
        """Bug 777475: The noinclude filter and pyquery seems to really dislike
        empty string as input"""
        doc_src = ''
        result = kuma.wiki.content.filter_out_noinclude(doc_src)
        assert result == ''


class ExtractCodeSampleTests(UserTestCase):
    def test_sample_code_extraction(self):
        sample_html = u"""
            <div class="foo">
                <p>Hello world!</p>
                <p>Unicode fun: Przykłady 例 예제 示例</p>
            </div>
        """
        sample_css = u"""
            .foo p { color: red; }
        """
        sample_js = u"""
            window.alert("Hi there!");
        """
        rev = revision(is_approved=True, save=True, content=u"""
            <p>This is a page. Deal with it.</p>

            <h3 id="sample0">This is a section</h3>
            <pre class="brush:html; highlight: [5, 15]; html-script: true">section html</pre>
            <pre class="brush:css;">section css</pre>
            <pre class="brush: js">section js</pre>

            <h3>The following is a new section</h3>

            <div id="sample1" class="code-sample">
                <pre class="brush: html;">Ignore me</pre>
                <pre class="brush:css;">Ignore me</pre>
                <pre class="brush: js">Ignore me</pre>
            </div>

            <ul id="sample2" class="code-sample">
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

            <p>More content shows up here.</p>
            <p id="not-a-sample">This isn't a sample, but it
                shouldn't cause an error</p>

            <h4 id="sample3">Another section</h4>
            <pre class="brush: html">Ignore me</pre>
            <pre class="brush: js">Ignore me</pre>

            <h4>Yay a header</h4>
            <p>Yadda yadda</p>

            <div id="sample4" class="code-sample">
                <pre class="brush: js">Ignore me</pre>
            </div>

            <p>Yadda yadda</p>
        """ % (escape(sample_html), escape(sample_css), escape(sample_js)))

        # live sample using the section logic
        result = rev.document.extract.code_sample('sample0')
        eq_('section html', result['html'].strip())
        eq_('section css', result['css'].strip())
        eq_('section js', result['js'].strip())

        # pull out a complete sample.
        result = rev.document.extract.code_sample('sample2')
        eq_(sample_html.strip(), result['html'].strip())
        eq_(sample_css.strip(), result['css'].strip())
        eq_(sample_js.strip(), result['js'].strip())

        # a sample missing one part.
        result = rev.document.extract.code_sample('sample3')
        eq_('Ignore me', result['html'].strip())
        eq_(None, result['css'])
        eq_('Ignore me', result['js'].strip())

        # a sample with only one part.
        result = rev.document.extract.code_sample('sample4')
        eq_(None, result['html'])
        eq_(None, result['css'])
        eq_('Ignore me', result['js'].strip())

        # a "sample" with no code listings.
        result = rev.document.extract.code_sample('not-a-sample')
        eq_(None, result['html'])
        eq_(None, result['css'])
        eq_(None, result['js'])

    def test_bug819999(self):
        """
        Non-breaking spaces are turned to normal spaces in code sample
        extraction.
        """
        rev = revision(is_approved=True, save=True, content="""
            <h2 id="bug819999">Bug 819999</h2>
            <pre class="brush: css">
            .widget select,
            .no-widget .select {
            &nbsp; position : absolute;
            &nbsp; left&nbsp;&nbsp;&nbsp;&nbsp; : -5000em;
            &nbsp; height&nbsp;&nbsp; : 0;
            &nbsp; overflow : hidden;
            }
            </pre>
        """)
        result = rev.document.extract.code_sample('bug819999')
        ok_(result['css'].find(u'\xa0') == -1)

    def test_bug1284781(self):
        """
        Non-breaking spaces are turned to normal spaces in code sample
        extraction.
        """
        rev = revision(is_approved=True, save=True, content="""
            <h2 id="bug1284781">Bug 1284781</h2>
            <pre class="brush: css">
            .widget select,
            .no-widget .select {
            &nbsp; position : absolute;
            &nbsp; left&nbsp;&nbsp;&nbsp;&nbsp; : -5000em;
            &nbsp; height&nbsp;&nbsp; : 0;
            &nbsp; overflow : hidden;
            }
            </pre>
        """)
        result = rev.document.extract.code_sample('bug1284781')
        ok_(result['css'].find(u'&nbsp;') == -1)

    def test_bug1173170(self):
        """
        Make sure the colons in sample ids doesn't trip up the code
        extraction due to their ambiguity with pseudo selectors
        """
        rev = revision(is_approved=True, save=True,
                       content="""<pre id="Bug:1173170">Bug 1173170</pre>""")
        rev.document.extract.code_sample('Bug:1173170')  # No SelectorSyntaxError


class BugizeTests(TestCase):
    def test_bugize_text(self):
        bad = 'Fixing bug #12345 again. <img src="http://davidwalsh.name" /> <a href="">javascript></a>'
        good = 'Fixing <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345" target="_blank">bug 12345</a> again. &lt;img src=&#34;http://davidwalsh.name&#34; /&gt; &lt;a href=&#34;&#34;&gt;javascript&gt;&lt;/a&gt;'
        eq_(bugize_text(bad), Markup(good))

        bad_upper = 'Fixing Bug #12345 again.'
        good_upper = 'Fixing <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345" target="_blank">Bug 12345</a> again.'
        eq_(bugize_text(bad_upper), Markup(good_upper))


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

    pattern = r'^https?\:\/\/(sample|test)server'
    result_src = parse(doc_src).filterIframeHosts(pattern).serialize()
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
    pattern = r'https?\:\/\/sampleserver'
    result_src = parse(doc_src).filterIframeHosts(pattern).serialize()
    assert normalize_html(expected_src) == normalize_html(result_src)


FILTERIFRAME_ACCEPTED = {
    'stage': ('https://stage-files.mdn.moz.works/'
              'fr/docs/Test$samples/sample2?revision=234'),
    'scl3-stage': ('https://developer.allizom.org/'
                   'fr/docs/Test$samples/sample2?revision=234'),
    'test': 'http://testserver/en-US/docs/Test$samples/test?revision=567',
    'docker': 'http://localhost:8000/de/docs/Test$samples/test?revision=678',
    'youtube_http': ('http://www.youtube.com/embed/'
                     'iaNoBlae5Qw/?feature=player_detailpage'),
    'youtube_ssl': ('https://youtube.com/embed/'
                    'iaNoBlae5Qw/?feature=player_detailpage'),
    'prod': ('https://mdn.mozillademos.org/'
             'en-US/docs/Web/CSS/text-align$samples/alignment?revision=456'),
    'newrelic': 'https://rpm.newrelic.com/public/charts/9PqtkrTkoo5',
    'jsfiddle': 'https://jsfiddle.net/78dg25ax/embedded/js,result/',
    'github.io': ('https://mdn.github.io/webgl-examples/'
                  'tutorial/sample6/index.html'),
    'ie_moz_net': ('https://interactive-examples.mdn.mozilla.net/'
                   'pages/js/array-push.html'),
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
}


@pytest.mark.parametrize('url', FILTERIFRAME_ACCEPTED.values(),
                         ids=FILTERIFRAME_ACCEPTED.keys())
def test_filteriframe_default_accepted(url):
    doc_src = '<iframe id="test" src="%s"></iframe>' % url
    pattern = settings.CONSTANCE_CONFIG['KUMA_WIKI_IFRAME_ALLOWED_HOSTS'][0]
    result_src = parse(doc_src).filterIframeHosts(pattern).serialize()
    page = pq(result_src)
    assert page('#test').attr('src') == url


@pytest.mark.parametrize('url', FILTERIFRAME_REJECTED.values(),
                         ids=FILTERIFRAME_REJECTED.keys())
def test_filteriframe_default_rejected(url):
    doc_src = '<iframe id="test" src="%s"></iframe>' % url
    pattern = settings.CONSTANCE_CONFIG['KUMA_WIKI_IFRAME_ALLOWED_HOSTS'][0]
    result_src = parse(doc_src).filterIframeHosts(pattern).serialize()
    page = pq(result_src)
    assert page('#test').attr('src') == ''


class BleachTests(TestCase):
    def test_bleach_filter_invalid_protocol(self):
        doc_src = """
            <p><a id="xss" href="data:text/html;base64,PHNjcmlwdD5hbGVydCgiZG9jdW1lbnQuY29va2llOiIgKyBkb2N1bWVudC5jb29raWUpOzwvc2NyaXB0Pg==">click for xss</a></p>
            <p><a id="xss2" class="no-track" href=" data:text/html;base64,PHNjcmlwdD5hbGVydChkb2N1bWVudC5kb21haW4pPC9zY3JpcHQ+">click me</a>
            <p><a id="xss3" class="no-track" href="
                data:text/html;base64,PHNjcmlwdD5hbGVydChkb2N1bWVudC5kb21haW4pPC9zY3JpcHQ+">click me</a>
            <p><a id="ok" href="/docs/ok/test">OK link</a></p>
        """
        result_src = bleach.clean(doc_src,
                                  tags=ALLOWED_TAGS,
                                  attributes=ALLOWED_ATTRIBUTES,
                                  protocols=ALLOWED_PROTOCOLS)
        page = pq(result_src)

        eq_(page.find('#xss').attr('href'), None)
        eq_(page.find('#xss2').attr('href'), None)
        eq_(page.find('#xss3').attr('href'), None)
        eq_(page.find('#ok').attr('href'), '/docs/ok/test')


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
        assert url.startswith(AL_BASE_URL)
    else:
        url = root_doc.get_absolute_url()
    if anchor == 'withAnchor':
        url += "#anchor"
    if has_class == 'hasClass':
        link_class = ' class="extra"'
    else:
        link_class = ''
    html = normalize_html('<li><a %s href="%s"></li>' % (link_class, url))
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


@pytest.mark.parametrize('has_class', ('hasClass', 'noClass'))
@pytest.mark.parametrize('anchor', ('withAnchor', 'noAnchor'))
@pytest.mark.parametrize('full_url', ('fullURL', 'pathOnly'))
def test_annotate_links_nonexisting_doc(db, anchor, full_url, has_class):
    """Links to existing docs are unmodified."""
    url = 'en-US/docs/Root'
    if full_url == 'fullURL':
        url = urljoin(AL_BASE_URL, url)
    if anchor == 'withAnchor':
        url += "#anchor"
    if has_class == 'hasClass':
        link_class = ' class="extra"'
        expected_class = ' class="extra new"'
    else:
        link_class = ''
        expected_class = ' class="new"'
    html = '<li><a %s href="%s"></li>' % (link_class, url)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    expected_raw = '<li><a %s href="%s"></li>' % (expected_class, url)
    assert normalize_html(actual_raw) == normalize_html(expected_raw)


def test_annotate_links_uilocale_to_existing_doc(root_doc):
    """Links to existing docs with embeded locales are unmodified."""
    assert root_doc.get_absolute_url() == '/en-US/docs/Root'
    url = '/en-US/docs/en-US/Root'  # Notice the 'en-US' after '/docs/'
    html = normalize_html('<li><a href="%s"></li>' % url)
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    assert normalize_html(actual_raw) == html


def test_annotate_links_uilocale_to_nonexisting_doc(db):
    """Links to new docs with embeded locales are unmodified."""
    url = '/en-US/docs/en-US/Root'  # Notice the 'en-US' after '/docs/'
    html = '<li><a href="%s"></li>' % url
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    expected = normalize_html('<li><a class="new" href="%s"></li>' % url)
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


def test_annotate_links_external_link():
    """Links to external sites get an external class."""
    html = '<li><a href="https://mozilla.org">External link</a>.</li>'
    actual_raw = parse(html).annotateLinks(base_url=AL_BASE_URL).serialize()
    expected = normalize_html(
        '<li><a class="external" href="https://mozilla.org">'
        'External link</a>.</li>')
    assert normalize_html(actual_raw) == expected


class FilterEditorSafetyTests(TestCase):
    def test_editor_safety_filter(self):
        """Markup that's hazardous for editing should be stripped"""
        doc_src = """
            <svg><circle onload=confirm(3)>
            <h1 class="header1">Header One</h1>
            <p>test</p>
            <section>
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
        eq_(normalize_html(expected_src), normalize_html(result_src))


class AllowedHTMLTests(KumaTestCase):
    simple_tags = (
        'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre',
        'code', 'dl', 'dt', 'dd', 'table',
        'section', 'header', 'footer',
        'nav', 'article', 'aside', 'figure', 'dialog', 'hgroup',
        'mark', 'time', 'meter', 'output', 'progress',
        'audio', 'details', 'datagrid', 'datalist', 'table',
        'address'
    )

    unclose_tags = ('img', 'input', 'br', 'command')

    special_tags = (
        "<table><thead><tr><th>foo</th></tr></thead><tbody><tr><td>foo</td></tr></tbody></table>",
    )

    special_attributes = (
        '<command id="foo">',
        '<img align="left" alt="picture of foo" class="foo" dir="rtl" id="foo" src="foo" title="foo">',
        '<a class="foo" href="foo" id="foo" title="foo">foo</a>',
        '<div class="foo">foo</div>',
        '<video class="movie" controls id="some-movie" lang="en-US" src="some-movie.mpg">Fallback</video>'
        # TODO: Styles have to be cleaned on a case-by-case basis. We
        # need to enumerate the styles we're going to allow, then feed
        # them to bleach.
        # '<span style="font-size: 24px"></span>',
    )

    def test_allowed_tags(self):
        for tag in self.simple_tags:
            html_str = '<%(tag)s></%(tag)s>' % {'tag': tag}
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))

        for tag in self.unclose_tags:
            html_str = '<%s>' % tag
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))

        for html_str in self.special_tags:
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))

    def test_allowed_attributes(self):
        for tag in ('div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre', 'code',
                    'dl', 'dt', 'dd', 'section', 'header', 'footer', 'nav',
                    'article', 'aside', 'figure', 'dialog', 'hgroup', 'mark',
                    'time', 'meter', 'output', 'progress', 'audio', 'details',
                    'datagrid', 'datalist', 'address'):
            html_str = '<%(tag)s id="foo"></%(tag)s>' % {'tag': tag}
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))

        for html_str in self.special_attributes:
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))

    def test_stripped_ie_comment(self):
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
        result = Document.objects.clean_content(content)
        eq_(normalize_html(expected), normalize_html(result))

    def test_iframe_in_script(self):
        """iframe in script should be filtered"""
        content = ('<script><iframe src="data:text/plain,foo">'
                   '</iframe></script>')
        expected = ('&lt;script&gt;&lt;iframe src="data:text/plain,foo"&gt;'
                    '&lt;/iframe&gt;&lt;/script&gt;')
        result = Document.objects.clean_content(content)
        eq_(normalize_html(expected), normalize_html(result))

    def test_iframe_in_style(self):
        """iframe in style should be filtered"""
        content = ('<style><iframe src="data:text/plain,foo">'
                   '</iframe></style>')
        expected = ('&lt;style&gt;&lt;iframe src="data:text/plain,foo"&gt;'
                    '&lt;/iframe&gt;&lt;/style&gt;')
        result = Document.objects.clean_content(content)
        eq_(normalize_html(expected), normalize_html(result))

    def test_iframe_in_textarea(self):
        """
        iframe in textarea should not be filtered since it's not parsed as tag
        """
        content = """
            <textarea><iframe src="data:text/plain,foo"></iframe></textarea>
        """
        expected = """
            <textarea><iframe src="data:text/plain,foo"></iframe></textarea>
        """
        result = Document.objects.clean_content(content)
        eq_(normalize_html(expected), normalize_html(result))


class ExtractorTests(UserTestCase):
    """Tests for document parsers that extract content"""

    def test_css_classname_extraction(self):
        expected = ('foobar', 'barfoo', 'bazquux')
        rev = revision(is_approved=True, save=True, content="""
            <p class="%s">Test</p>
            <p class="%s">Test</p>
            <div class="%s">Test</div>
        """ % expected)
        rev.document.render()
        result = rev.document.extract.css_classnames()
        eq_(sorted(expected), sorted(result))

    def test_html_attribute_extraction(self):
        expected = (
            'class="foobar"',
            'id="frazzy"',
            'lang="farb"',
        )
        rev = revision(is_approved=True, save=True, content="""
            <p %s>Test</p>
            <p %s>Test</p>
            <div %s>Test</div>
        """ % expected)
        rev.document.render()
        doc = Document.objects.get(pk=rev.document.pk)
        result = doc.extract.html_attributes()
        eq_(sorted(expected), sorted(result))

    def test_kumascript_macro_extraction(self):
        expected = ('foobar', 'barfoo', 'bazquux', 'banana')
        rev = revision(is_approved=True, save=True, content="""
            <p>{{ %s }}</p>
            <p>{{ %s("foo", "bar", "baz") }}</p>
            <p>{{ %s    ("quux") }}</p>
            <p>{{%s}}</p>
        """ % expected)
        result = rev.document.extract.macro_names()
        eq_(sorted(expected), sorted(result))

    @mock.patch('kuma.wiki.constants.CODE_SAMPLE_MACROS', ['LinkCodeSample'])
    def test_code_samples(self):
        expected = {
            'html': 'Some HTML',
            'css': '.some-css { color: red; }',
            'js': 'window.alert("HI THERE")',
        }
        rev = revision(is_approved=True, save=True, content="""
            <div id="sample" class="code-sample">
                <pre class="brush: html">%(html)s</pre>
                <pre class="brush: css">%(css)s</pre>
                <pre class="brush: js">%(js)s</pre>
            </div>
            {{ LinkCodeSample('sample1') }}
        """ % expected)
        result = rev.document.extract.code_sample('sample')
        eq_(expected, result)

    @mock.patch('kuma.wiki.constants.CODE_SAMPLE_MACROS', ['LinkCodeSample'])
    def test_code_samples_with_null_character_in_sample_name(self):
        rev = revision(is_approved=True, save=True, content="""
            <div id="sample" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            {{ LinkCodeSample('sample1') }}
        """)
        # The real test here is to ensure that no exception is raised, but
        # might as well also check that the sample section was not found.
        sample_name = u"sam\x00ple"  # Null character in name
        result = rev.document.extract.code_sample(sample_name)
        eq_(dict(html=None, css=None, js=None), result)

    @mock.patch('kuma.wiki.constants.CODE_SAMPLE_MACROS', ['LinkCodeSample'])
    def test_code_samples_with_escapable_characters_in_sample_name(self):
        rev = revision(is_approved=True, save=True, content="""
            <div id="sample" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            {{ LinkCodeSample('sample1') }}
        """)
        # The real test here is to ensure that no exception is raised, but
        # might as well also check that the sample section was not found.
        sample_name = u"""sam<'&">ple"""  # One of "<>'& in name
        result = rev.document.extract.code_sample(sample_name)
        eq_(dict(html=None, css=None, js=None), result)


class GetSEODescriptionTests(KumaTestCase):

    def test_summary_section(self):
        content = (
            '<h2 id="Summary">Summary</h2><p>The <strong>Document Object '
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
        expected = (
            'The Document Object Model (DOM) is an API for HTML and '
            'XML documents. It provides a structural representation of the'
            ' document, enabling you to modify its content and visual'
            ' presentation by using a scripting language such as'
            ' JavaScript.')
        eq_(expected, get_seo_description(content, 'en-US'))

    def test_keep_markup(self):
        content = """
            <h2 id="Summary">Summary</h2>
            <p>The <strong>Document Object Model </strong>
            (<strong>DOM</strong>) is an API for <a href="/en-US/docs/HTML"
            title="en-US/docs/HTML">HTML</a> and <a href="/en-US/docs/XML"
            title="en-US/docs/XML">XML</a> documents. It provides a structural
            representation of the document, enabling you to modify its content
            and visual presentation by using a scripting language such as <a
            href="/en-US/docs/JavaScript"
            title="https://developer.mozilla.org/en-US/docs/JavaScript">
            JavaScript</a>.</span></p>
         """
        expected = """
            The <strong>Document Object Model </strong>
            (<strong>DOM</strong>) is an API for <a href="/en-US/docs/HTML"
            title="en-US/docs/HTML">HTML</a> and <a href="/en-US/docs/XML"
            title="en-US/docs/XML">XML</a> documents. It provides a structural
            representation of the document, enabling you to modify its content
            and visual presentation by using a scripting language such as <a
            href="/en-US/docs/JavaScript"
            title="https://developer.mozilla.org/en-US/docs/JavaScript">
            JavaScript</a>.</span>
        """
        eq_(normalize_html(expected),
            normalize_html(get_seo_description(content, 'en-US', False)))

    def test_html_elements_spaces(self):
        # No spaces with html tags
        content = (
            u'<p><span class="seoSummary">The <strong>Document Object '
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
        expected = (
            'The Document Object Model (DOM) is an API for HTML and '
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

    def test_empty_paragraph_content(self):
        content = u'''<p></p><div class="overheadIndicator draft draftHeader">
            <strong>DRAFT</strong>
                <div>This page is not complete.</div>
                </div><p></p>
                <p></p><div class="note"><strong>Note:</strong> Please do not
                translate this page until it is done; it will be much easier at
                that point. The French translation is a test to be sure that it
                works well.</div><p></p>'''
        expected = ('')
        eq_(expected, get_seo_description(content, 'en-US', False))
