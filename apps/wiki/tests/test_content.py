# This Python file uses the following encoding: utf-8
# see also: http://www.python.org/dev/peps/pep-0263/
import logging
from urlparse import urljoin
from jinja2 import escape

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from pyquery import PyQuery as pq
import bleach

from sumo.tests import TestCase
import wiki.content
from wiki.content import (CodeSyntaxFilter, DekiscriptMacroFilter,
                          SectionTOCFilter, SectionIDFilter, IframeHostFilter,
                          SECTION_TAGS)
from wiki.models import ALLOWED_TAGS, ALLOWED_ATTRIBUTES, Document
from wiki.tests import normalize_html, doc_rev, document, revision


class ContentSectionToolTests(TestCase):
    fixtures = ['test_users.json']

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
        """

        result_src = (wiki.content
                      .parse(doc_src)
                      .injectSectionIDs()
                      .serialize())
        result_doc = pq(result_src)

        expected = (
            ('header1', 'Header_One'),
            ('header2', 'Header_Two'),
            ('hasname', 'Constants'),
            ('hasid',   'This_text_clobbers_the_ID'),
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
        result = (wiki.content
                  .parse(doc_src)
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
        result = (wiki.content
                  .parse(doc_src)
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
        result = (wiki.content
                  .parse(doc_src)
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
        result = (wiki.content
                  .parse(doc_src)
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
        result = (wiki.content
                  .parse(doc_src)
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
        result = (wiki.content
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
        result = (wiki.content
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
        result = (wiki.content
                  .parse(doc_src)
                  .filter(CodeSyntaxFilter).serialize())
        eq_(normalize_html(expected), normalize_html(result))

    def test_non_ascii_section_headers(self):
        headers = [
           (u'Documentation à propos de HTML',
            'Documentation_.C3.A0_propos_de_HTML'),
            (u'Outils facilitant le développement HTML',
             'Outils_facilitant_le_d.C3.A9veloppement_HTML'),
            (u'例:\u00a0スキューと平行移動',
             '.E4.BE.8B.3A.C2.A0.E3.82.B9.E3.82.AD.E3.83.A5.E3.83.BC.E3.81.A8.E5.B9.B3.E8.A1.8C.E7.A7.BB.E5.8B.95'),
            (u'例:\u00a0回転',
             '.E4.BE.8B.3A.C2.A0.E5.9B.9E.E8.BB.A2'),
            (u'Documentação',
             'Documenta.C3.A7.C3.A3o'),
            (u'Lektury uzupełniające',
             'Lektury_uzupe.C5.82niaj.C4.85ce'),
            (u'Атрибуты',
             '.D0.90.D1.82.D1.80.D0.B8.D0.B1.D1.83.D1.82.D1.8B'),
            (u'HTML5 엘리먼트',
             'HTML5_.EC.97.98.EB.A6.AC.EB.A8.BC.ED.8A.B8'),
            (u'Non safe title "#$%&+,/:;=?@[\\]^`{|}~',
             u'Non_safe_title_.22.23.24.25.26.2B.2C.2F.3A.3B.3D.3F.40.5B.5C.5D.5E.60.7B.7C.7D.7E'),
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
        result = (wiki.content
                  .parse(doc_src)
                  .filter(SectionTOCFilter).serialize())
        eq_(normalize_html(expected), normalize_html(result))

    def test_dekiscript_macro_conversion(self):
        doc_src = u"""
            <span>Just a span</span>
            <span class="notascript">Hi there</span>
            <li><span class="script">Warning("Performing synchronous IO on the main thread can cause serious performance problems. As a result, this method of modifying the database is <strong>strongly</strong> discouraged!")</span></li>
            <li><span class="script">Note("Performing synchronous IO on the main thread can cause serious performance problems. As a result, this method of modifying the database is <strong class="important">strongly</strong> discouraged!")</span></li>
            <li><span class="script">MixedCaseName('parameter1', 'parameter2')</span></li>
            <li><span class="script">template.lowercasename('border')</span></li>
            <li><span class="script">Template.UpperCaseTemplate("foo")</span></li>
            <li><span class="script">wiki.template('英語版章題', [ "Reusing tabs" ])</span></li>
            <li><span class="script">template("non-standard_inline", ["Reusing tabs", "YAY"])</span></li>
            <li><span class="script">wiki.template('英語版章題')</span></li>
            <li><span class="script">template("non-standard_inline")</span></li>
        """
        expected = u"""
            <span>Just a span</span>
            <span class="notascript">Hi there</span>
            <li>{{ Warning("Performing synchronous IO on the main thread can cause serious performance problems. As a result, this method of modifying the database is <strong>strongly</strong> discouraged!") }}</li>
            <li>{{ Note("Performing synchronous IO on the main thread can cause serious performance problems. As a result, this method of modifying the database is <strong class="important">strongly</strong> discouraged!") }}</li>
            <li>{{ MixedCaseName('parameter1', 'parameter2') }}</li>
            <li>{{ lowercasename('border') }}</li>
            <li>{{ UpperCaseTemplate("foo") }}</li>
            <li>{{ 英語版章題("Reusing tabs") }}</li>
            <li>{{ non-standard_inline("Reusing tabs", "YAY") }}</li>
            <li>{{ 英語版章題() }}</li>
            <li>{{ non-standard_inline() }}</li>
        """

        # Check line-by-line, to help work out any issues failure-by-failure
        doc_src_lines = doc_src.split("\n")
        expected_lines = expected.split("\n")
        for i in range(0, len(doc_src_lines)):
            result = (wiki.content
                      .parse(doc_src_lines[i])
                      .filter(DekiscriptMacroFilter).serialize())
            eq_(normalize_html(expected_lines[i]), normalize_html(result))

        # But, the whole thing should work in the filter, as well.
        result = (wiki.content
                  .parse(doc_src)
                  .filter(DekiscriptMacroFilter).serialize())
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
        result = (wiki.content.filter_out_noinclude(doc_src))
        eq_(normalize_html(expected), normalize_html(result))

    def test_noinclude_empty_content(self):
        """Bug 777475: The noinclude filter and pyquery seems to really dislike
        empty string as input"""
        doc_src = ''
        try:
            result = wiki.content.filter_out_noinclude(doc_src)
            eq_('', result)
        except e:
            ok_(False, "There should not have been an exception")

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
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Ignore me</pre>
                <pre class="brush: css">Ignore me</pre>
                <pre class="brush: js">Ignore me</pre>
            </div>
            <ul id="sample2" class="code-sample">
                <li><span>HTML</span>
                    <pre class="brush: html">%s</pre>
                </li>
                <li><span>CSS</span>
                    <pre class="brush: css">%s</pre>
                </li>
                <li><span>JS</span>
                    <pre class="brush: js">%s</pre>
                </li>
            </ul>
            <p>More content shows up here.</p>
            <p id="not-a-sample">This isn't a sample, but it shouldn't cause an
                error</p>
            <div id="sample3" class="code-sample">
                <pre class="brush: html">Ignore me</pre>
                <pre class="brush: js">Ignore me</pre>
            </div>
            <p>Yadda yadda</p>
            <div id="sample4" class="code-sample">
                <pre class="brush: js">Ignore me</pre>
            </div>
            <p>Yadda yadda</p>
        """ % (escape(sample_html), escape(sample_css), escape(sample_js))

        # First, pull out a complete sample.
        result = wiki.content.extract_code_sample('sample2', doc_src)
        eq_(sample_html.strip(), result['html'].strip())
        eq_(sample_css.strip(), result['css'].strip())
        eq_(sample_js.strip(), result['js'].strip())

        # Now, a sample missing one part.
        result = wiki.content.extract_code_sample('sample3', doc_src)
        eq_('Ignore me', result['html'].strip())
        eq_(None, result['css'])
        eq_('Ignore me', result['js'].strip())

        # Now, a sample with only one part.
        result = wiki.content.extract_code_sample('sample4', doc_src)
        eq_(None, result['html'])
        eq_(None, result['css'])
        eq_('Ignore me', result['js'].strip())

        # Finally, a "sample" with no code listings.
        result = wiki.content.extract_code_sample('not-a-sample', doc_src)
        eq_(None, result['html'])
        eq_(None, result['css'])
        eq_(None, result['js'])

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

        result_src = (wiki.content.parse(doc_src)
                      .filterIframeHosts(['sampleserver'])
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

    def test_link_annotation(self):
        d, r = doc_rev("This document exists")
        d.save()
        r.save()

        d2 = document(title=u'Héritée', locale=u'fr', slug=u'CSS/Héritage',
                      save=True)

        base_url = u'http://testserver/'
        vars = dict(
            base_url=base_url,
            exist_url=d.get_absolute_url(),
            exist_url_with_base=urljoin(base_url, d.get_absolute_url()),
            uilocale_url=u'/en-US/docs/%s/%s' % (d.locale, d.slug),
            noexist_url=u'/en-US/docs/no-such-doc',
            noexist_url_with_base=urljoin(base_url, u'/en-US/docs/no-such-doc'),
            noexist_uilocale_url=u'/en-US/docs/en-US/blah-blah-blah',
            nonen_slug='/fr/docs/CSS/H%c3%a9ritage',
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
        """ % vars

        # Split the markup into lines, to better see failures
        doc_lines = doc_src.strip().split("\n")
        expected_lines = expected.strip().split("\n")
        for idx in range(0, len(doc_lines)):
            doc_line = doc_lines[idx]
            expected_line = expected_lines[idx]
            result_line = (wiki.content.parse(doc_line)
                          .annotateLinks(base_url=vars['base_url'])
                          .serialize())
            eq_(normalize_html(expected_line), normalize_html(result_line))


class AllowedHTMLTests(TestCase):
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
        '<img align="left" alt="picture of foo" class="foo" id="foo" src="foo" title="foo">',
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
        for tag in ('div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre', 'code', 'dl', 'dt', 'dd',
                    'section', 'header', 'footer', 'nav', 'article', 'aside', 'figure',
                    'dialog', 'hgroup', 'mark', 'time', 'meter', 'output',
                    'progress', 'audio', 'details', 'datagrid', 'datalist',
                    'address'):
            html_str = '<%(tag)s id="foo"></%(tag)s>' % {'tag': tag}
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))

        for html_str in self.special_attributes:
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))
