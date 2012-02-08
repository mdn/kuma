import logging

from datetime import datetime, timedelta

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from pyquery import PyQuery as pq

from django.core.exceptions import ValidationError

from sumo import ProgrammingError
from sumo.tests import TestCase
import wiki.content
from wiki.content import (SectionIDFilter, SECTION_EDIT_TAGS)
from wiki.tests import normalize_html

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter

import bleach
from wiki.models import ALLOWED_TAGS, ALLOWED_ATTRIBUTES


class ContentSectionToolTests(TestCase):
    
    def test_section_ids(self):

        doc_src = """
            <h1>head</h1>
            <p>test</p>
            <section>
                <h1>head</h1>
                <p>test</p>
            </section>
            <h2>head</h2>
            <p>test</p>

            <h1 id="i-already-have-an-id" class="hasid">head</h1>

            <h1>head</h1>
            <p>test</p>
        """

        result_src = (wiki.content
                      .parse(doc_src)
                      .injectSectionIDs()
                      .serialize())
        result_doc = pq(result_src)

        # First, ensure an existing ID hasn't been disturbed
        eq_('i-already-have-an-id', result_doc.find('.hasid').attr('id'))

        # Then, ensure all elements in need of an ID now all have unique IDs.
        ok_(len(SECTION_EDIT_TAGS) > 0)
        els = result_doc.find(', '.join(SECTION_EDIT_TAGS))
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


class AllowedHTMLTests(TestCase):
    simple_tags = (
        'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'pre',
        'code', 'dl', 'dt', 'dd', 'table',
        'section', 'header', 'footer',
        'nav', 'article', 'aside', 'figure', 'dialog', 'hgroup',
        'mark', 'time', 'meter', 'output', 'progress',
        'audio', 'video', 'details', 'datagrid', 'datalist', 'table',
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
                    'progress', 'audio', 'video', 'details', 'datagrid', 'datalist',
                    'address'):
            html_str = '<%(tag)s id="foo"></%(tag)s>' % {'tag': tag}
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))

        for html_str in self.special_attributes:
            eq_(html_str, bleach.clean(html_str, attributes=ALLOWED_ATTRIBUTES,
                                       tags=ALLOWED_TAGS))
