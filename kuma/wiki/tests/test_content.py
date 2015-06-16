# -*- coding: utf-8 -*-
from urlparse import urljoin

import bleach
from jinja2 import escape, Markup
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from kuma.core.tests import KumaTestCase
from kuma.users.tests import UserTestCase
import kuma.wiki.content
from ..constants import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from ..content import (CodeSyntaxFilter, SectionTOCFilter, SectionIDFilter,
                       H2TOCFilter, H3TOCFilter, SECTION_TAGS,
                       get_seo_description, get_content_sections,
                       extract_css_classnames, extract_html_attributes,
                       extract_kumascript_macro_names)
from ..helpers import bugize_text
from ..models import Document
from . import normalize_html, doc_rev, document


class ContentSectionToolTests(UserTestCase):

    def test_section_pars_for_empty_docs(self):
        doc = document(title='Doc', locale=u'fr', slug=u'doc', save=True,
                       html='<!-- -->')
        res = get_content_sections(doc.html)
        eq_(type(res).__name__, 'list')

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

    @attr('toc')
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

    @attr('toc')
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

    @attr('toc')
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
        try:
            result = kuma.wiki.content.filter_out_noinclude(doc_src)
            eq_('', result)
        except:
            self.fail("There should not have been an exception")

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
        doc_src = u"""
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
        """ % (escape(sample_html), escape(sample_css), escape(sample_js))

        # live sample using the section logic
        result = kuma.wiki.content.extract_code_sample('sample0', doc_src)
        eq_('section html', result['html'].strip())
        eq_('section css', result['css'].strip())
        eq_('section js', result['js'].strip())

        # pull out a complete sample.
        result = kuma.wiki.content.extract_code_sample('sample2', doc_src)
        eq_(sample_html.strip(), result['html'].strip())
        eq_(sample_css.strip(), result['css'].strip())
        eq_(sample_js.strip(), result['js'].strip())

        # a sample missing one part.
        result = kuma.wiki.content.extract_code_sample('sample3', doc_src)
        eq_('Ignore me', result['html'].strip())
        eq_(None, result['css'])
        eq_('Ignore me', result['js'].strip())

        # a sample with only one part.
        result = kuma.wiki.content.extract_code_sample('sample4', doc_src)
        eq_(None, result['html'])
        eq_(None, result['css'])
        eq_('Ignore me', result['js'].strip())

        # a "sample" with no code listings.
        result = kuma.wiki.content.extract_code_sample('not-a-sample', doc_src)
        eq_(None, result['html'])
        eq_(None, result['css'])
        eq_(None, result['js'])

    def test_bug819999(self):
        """Non-breaking spaces are turned to normal spaces in code sample
        extraction."""
        doc_src = """
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
        """
        result = kuma.wiki.content.extract_code_sample('bug819999', doc_src)
        ok_(result['css'].find(u'\xa0') == -1)

    def test_bugize_text(self):
        bad = 'Fixing bug #12345 again. <img src="http://davidwalsh.name" /> <a href="">javascript></a>'
        good = 'Fixing <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345" target="_blank">bug 12345</a> again. &lt;img src=&#34;http://davidwalsh.name&#34; /&gt; &lt;a href=&#34;&#34;&gt;javascript&gt;&lt;/a&gt;'
        eq_(bugize_text(bad), Markup(good))

        bad_upper = 'Fixing Bug #12345 again.'
        good_upper = 'Fixing <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345" target="_blank">Bug 12345</a> again.'
        eq_(bugize_text(bad_upper), Markup(good_upper))

    def test_iframe_host_filter(self):
        slug = 'test-code-embed'
        embed_url = 'https://sampleserver/en-US/docs/%s$samples/sample1' % slug

        doc_src = """
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <iframe id="if1" src="%(embed_url)s"></iframe>
            <iframe id="if2" src="http://testserver"></iframe>
            <iframe id="if3" src="https://some.alien.site.com"></iframe>
            <p>test</p>
        """ % dict(embed_url=embed_url)

        result_src = (kuma.wiki.content.parse(doc_src)
                      .filterIframeHosts('^https?\:\/\/sampleserver')
                      .serialize())
        page = pq(result_src)

        if1 = page.find('#if1')
        eq_(if1.length, 1)
        eq_(if1.attr('src'), embed_url)

        if2 = page.find('#if2')
        eq_(if2.length, 1)
        eq_(if2.attr('src'), '')

        if3 = page.find('#if3')
        eq_(if3.length, 1)
        eq_(if3.attr('src'), '')

    def test_iframe_host_filter_invalid_host(self):
        doc_src = """
            <iframe id="if1" src="http://sampleserver"></iframe>
            <iframe id="if2" src="http://testserver"></iframe>
            <iframe id="if3" src="http://davidwalsh.name"></iframe>
            <iframe id="if4" src="ftp://davidwalsh.name"></iframe>
            <p>test</p>
        """
        result_src = (kuma.wiki.content.parse(doc_src)
                      .filterIframeHosts('^https?\:\/\/(sample|test)server')
                      .serialize())
        page = pq(result_src)

        eq_(page.find('#if1').attr('src'), 'http://sampleserver')
        eq_(page.find('#if2').attr('src'), 'http://testserver')
        eq_(page.find('#if3').attr('src'), '')
        eq_(page.find('#if4').attr('src'), '')

    def test_iframe_host_filter_youtube(self):
        tubes = (
            'http://www.youtube.com/embed/iaNoBlae5Qw/?feature=player_detailpage',
            'https://youtube.com/embed/iaNoBlae5Qw/?feature=player_detailpage',
            'https://youtube.com/sembed/'
        )
        doc_src = """
            <iframe id="if1" src="%s"></iframe>
            <iframe id="if2" src="%s"></iframe>
            <iframe id="if3" src="%s"></iframe>
            <p>test</p>
        """ % tubes
        result_src = (kuma.wiki.content.parse(doc_src)
                      .filterIframeHosts('^https?\:\/\/(www.)?youtube.com\/embed\/(\.*)')
                      .serialize())
        page = pq(result_src)

        eq_(page.find('#if1').attr('src'), tubes[0])
        eq_(page.find('#if2').attr('src'), tubes[1])
        eq_(page.find('#if3').attr('src'), '')

    def test_iframe_host_contents_filter(self):
        """Any contents inside an <iframe> should be removed"""
        doc_src = """
            <iframe>
            <iframe src="javascript:alert(1);"></iframe>
            </iframe>
        """
        expected_src = """
            <iframe>
            </iframe>
        """
        result_src = (kuma.wiki.content.parse(doc_src)
                      .filterIframeHosts('^https?\:\/\/sampleserver')
                      .serialize())
        eq_(normalize_html(expected_src), normalize_html(result_src))

    def test_link_annotation(self):
        d, r = doc_rev("This document exists")
        d.save()
        r.save()

        document(title=u'Héritée', locale=u'fr', slug=u'CSS/Héritage',
                 save=True)
        document(title=u'DOM/StyleSheet', locale=u'en-US',
                 slug=u'DOM/StyleSheet', save=True)

        base_url = u'https://testserver'
        vars = dict(
            base_url=base_url,
            exist_url=d.get_absolute_url(),
            exist_url_with_base=urljoin(base_url, d.get_absolute_url()),
            uilocale_url=u'/en-US/docs/%s/%s' % (d.locale, d.slug),
            noexist_url=u'/en-US/docs/no-such-doc',
            noexist_url_with_base=urljoin(base_url,
                                          u'/en-US/docs/no-such-doc'),
            noexist_uilocale_url=u'/en-US/docs/en-US/blah-blah-blah',
            nonen_slug='/fr/docs/CSS/H%c3%a9ritage',
            tag_url='/en-US/docs/tag/foo',
            feed_url='/en-US/docs/feeds/atom/all',
            templates_url='/en-US/docs/templates',
        )
        doc_src = u"""
                <li><a href="%(nonen_slug)s">Héritée</a></li>
                <li><a href="%(exist_url)s">This doc should exist</a></li>
                <li><a href="%(exist_url)s#withanchor">This doc should exist</a></li>
                <li><a href="%(exist_url_with_base)s">This doc should exist</a></li>
                <li><a href="%(exist_url_with_base)s#withanchor">This doc should exist</a></li>
                <li><a href="%(uilocale_url)s">This doc should exist</a></li>
                <li><a class="foobar" href="%(exist_url)s">This doc should exist, and its class should be left alone.</a></li>
                <li><a href="%(noexist_url)s#withanchor">This doc should NOT exist</a></li>
                <li><a href="%(noexist_url)s">This doc should NOT exist</a></li>
                <li><a href="%(noexist_url_with_base)s">This doc should NOT exist</a></li>
                <li><a href="%(noexist_url_with_base)s#withanchor">This doc should NOT exist</a></li>
                <li><a href="%(noexist_uilocale_url)s">This doc should NOT exist</a></li>
                <li><a class="foobar" href="%(noexist_url)s">This doc should NOT exist, and its class should be altered</a></li>
                <li><a href="http://mozilla.org/">This is an external link</a></li>
                <li><a class="foobar" name="quux">A lack of href should not cause a problem.</a></li>
                <li><a>In fact, a "link" with no attributes should be no problem as well.</a></li>
                <a href="%(tag_url)s">Tag link</a>
                <a href="%(feed_url)s">Feed link</a>
                <a href="%(templates_url)s">Templates link</a>
                <a href="/en-US/docs/DOM/stylesheet">Case sensitive 1</a>
                <a href="/en-US/docs/DOM/Stylesheet">Case sensitive 1</a>
                <a href="/en-US/docs/DOM/StyleSheet">Case sensitive 1</a>
                <a href="/en-us/docs/dom/StyleSheet">Case sensitive 1</a>
                <a href="/en-US/docs/dom/Styles">For good measure</a>
        """ % vars
        expected = u"""
                <li><a href="%(nonen_slug)s">Héritée</a></li>
                <li><a href="%(exist_url)s">This doc should exist</a></li>
                <li><a href="%(exist_url)s#withanchor">This doc should exist</a></li>
                <li><a href="%(exist_url_with_base)s">This doc should exist</a></li>
                <li><a href="%(exist_url_with_base)s#withanchor">This doc should exist</a></li>
                <li><a href="%(uilocale_url)s">This doc should exist</a></li>
                <li><a class="foobar" href="%(exist_url)s">This doc should exist, and its class should be left alone.</a></li>
                <li><a class="new" href="%(noexist_url)s#withanchor">This doc should NOT exist</a></li>
                <li><a class="new" href="%(noexist_url)s">This doc should NOT exist</a></li>
                <li><a class="new" href="%(noexist_url_with_base)s">This doc should NOT exist</a></li>
                <li><a class="new" href="%(noexist_url_with_base)s#withanchor">This doc should NOT exist</a></li>
                <li><a class="new" href="%(noexist_uilocale_url)s">This doc should NOT exist</a></li>
                <li><a class="foobar new" href="%(noexist_url)s">This doc should NOT exist, and its class should be altered</a></li>
                <li><a class="external" href="http://mozilla.org/">This is an external link</a></li>
                <li><a class="foobar" name="quux">A lack of href should not cause a problem.</a></li>
                <li><a>In fact, a "link" with no attributes should be no problem as well.</a></li>
                <a href="%(tag_url)s">Tag link</a>
                <a href="%(feed_url)s">Feed link</a>
                <a href="%(templates_url)s">Templates link</a>
                <a href="/en-US/docs/DOM/stylesheet">Case sensitive 1</a>
                <a href="/en-US/docs/DOM/Stylesheet">Case sensitive 1</a>
                <a href="/en-US/docs/DOM/StyleSheet">Case sensitive 1</a>
                <a href="/en-us/docs/dom/StyleSheet">Case sensitive 1</a>
                <a class="new" href="/en-US/docs/dom/Styles">For good measure</a>
        """ % vars

        # Split the markup into lines, to better see failures
        doc_lines = doc_src.strip().split("\n")
        expected_lines = expected.strip().split("\n")
        for idx in range(0, len(doc_lines)):
            doc_line = doc_lines[idx]
            expected_line = expected_lines[idx]
            result_line = (kuma.wiki.content.parse(doc_line)
                                            .annotateLinks(
                                                base_url=vars['base_url'])
                                            .serialize())
            self.assertHTMLEqual(normalize_html(expected_line), normalize_html(result_line))

    @attr('bug821986')
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


class SearchParserTests(KumaTestCase):
    """Tests for document parsers that extract content for search indexing"""

    def test_css_classname_extraction(self):
        expected = ('foobar', 'barfoo', 'bazquux')
        content = """
            <p class="%s">Test</p>
            <p class="%s">Test</p>
            <div class="%s">Test</div>
        """ % expected
        result = extract_css_classnames(content)
        eq_(sorted(expected), sorted(result))

    def test_html_attribute_extraction(self):
        expected = (
            'class="foobar"',
            'id="frazzy"',
            'data-boof="farb"'
        )
        content = """
            <p %s>Test</p>
            <p %s>Test</p>
            <div %s>Test</div>
        """ % expected
        result = extract_html_attributes(content)
        eq_(sorted(expected), sorted(result))

    def test_kumascript_macro_extraction(self):
        expected = ('foobar', 'barfoo', 'bazquux', 'banana')
        content = """
            <p>{{ %s }}</p>
            <p>{{ %s("foo", "bar", "baz") }}</p>
            <p>{{ %s    ("quux") }}</p>
            <p>{{%s}}</p>
        """ % expected
        result = extract_kumascript_macro_names(content)
        eq_(sorted(expected), sorted(result))


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
