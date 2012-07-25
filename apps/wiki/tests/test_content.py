# This Python file uses the following encoding: utf-8
# see also: http://www.python.org/dev/peps/pep-0263/
import logging
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from pyquery import PyQuery as pq
import bleach

from sumo.tests import TestCase
import wiki.content
from wiki.content import (CodeSyntaxFilter, DekiscriptMacroFilter,
                          SectionTOCFilter, SectionIDFilter, SECTION_TAGS)
from wiki.models import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from wiki.tests import normalize_html


class ContentSectionToolTests(TestCase):

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
             '.E4.BE.8B:.C2.A0.E3.82.B9.E3.82.AD.E3.83.A5.E3.83.BC.E3.81.A8.E5.B9.B3.E8.A1.8C.E7.A7.BB.E5.8B.95'),
            (u'例:\u00a0回転',
             '.E4.BE.8B:.C2.A0.E5.9B.9E.E8.BB.A2'),
            (u'Documentação',
             'Documenta.C3.A7.C3.A3o'),
            (u'Lektury uzupełniające',
             'Lektury_uzupe.C5.82niaj.C4.85ce'),
            (u'Атрибуты',
             '.D0.90.D1.82.D1.80.D0.B8.D0.B1.D1.83.D1.82.D1.8B'),
            (u'HTML5 엘리먼트',
             'HTML5_.EC.97.98.EB.A6.AC.EB.A8.BC.ED.8A.B8'),
        ]

        section_filter = SectionIDFilter('')

        for original, slugified in headers:
            ok_(slugified == section_filter.slugify(original))


    @attr('toc')
    def test_generate_toc(self):
        doc_src = """
            <h1 id="HTML">HTML</h1>
              <h2 id="HTML5">HTML5</h2>
            <h1 id="JavaScript">JavaScript</h1>
              JavaScript is awesome.
              <h2 id="WebGL">WebGL</h2>
              <h2 id="Audio">Audio</h2>
                <h3 id="Audio-API">Audio API</h3>
            <h1 id="CSS">CSS</h1>
        """
        expected = """
            <li><a rel="internal" href="#HTML">HTML</a>
                <ol>
                  <li><a rel="internal" href="#HTML5">HTML5</a></li>
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
            <li><a rel="internal" href="#CSS">CSS</a></li>
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
