import logging

from datetime import datetime, timedelta

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from pyquery import PyQuery as pq

from django.core.exceptions import ValidationError

from sumo import ProgrammingError
from sumo.tests import TestCase
import wiki.content
from wiki.content import (SectionIDFilter)

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter


class ContentSectionToolTests(TestCase):
    
    def _normalize(self, input):
        """Normalize HTML5 input, discarding parts not significant for
        equivalence in tests"""

        class WhitespaceRemovalFilter(html5lib_Filter):
            def __iter__(self):
                for token in html5lib_Filter.__iter__(self):
                    if 'SpaceCharacters' == token['type']:
                        continue
                    yield token

        return (wiki.content
                .parse(unicode(input))
                .filter(WhitespaceRemovalFilter)
                .serialize())

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
        NEED_ID_TAGS = SectionIDFilter.NEED_ID_TAGS
        ok_(len(NEED_ID_TAGS) > 0)
        els = result_doc.find(', '.join(NEED_ID_TAGS))
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
        eq_(self._normalize(expected), self._normalize(result))

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
        eq_(self._normalize(expected), self._normalize(result))

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
        eq_(self._normalize(expected), self._normalize(result))

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
        eq_(self._normalize(expected), self._normalize(result))

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
        eq_(self._normalize(expected), self._normalize(result))

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
        eq_(self._normalize(expected), self._normalize(result))
