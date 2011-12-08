import logging

from datetime import datetime, timedelta

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from pyquery import PyQuery as pq

from django.core.exceptions import ValidationError

from sumo.tests import TestCase
import wiki.content
from wiki.forms import DocumentForm, RevisionForm, ReviewForm
from wiki.tests import (document, revision, doc_rev, translated_revision,
                        normalize_html)

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter


class FormSectionEditingTests(TestCase):
    fixtures = ['test_users.json']
    
    def test_form_loaded_with_section(self):
        """RevisionForm given section_id should load initial content for only
        one section"""
        d, r = doc_rev("""
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """)
        expected = """
            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>
        """
        rev_form = RevisionForm(instance=r, section_id="s2")
        eq_(normalize_html(expected), 
            normalize_html(rev_form.initial['content']))

    @attr('current')
    def test_form_save_section(self):
        d, r = doc_rev("""
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """)
        replace_content = """
            <h1 id="s2">New stuff</h1>
            <p>new stuff</p>
        """
        expected = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">New stuff</h1>
            <p>new stuff</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        rev_form = RevisionForm({"content": replace_content},
                                instance=r,
                                section_id="s2")
        new_rev = rev_form.save(r.creator, d)
        eq_(normalize_html(expected), 
            normalize_html(new_rev.content))

