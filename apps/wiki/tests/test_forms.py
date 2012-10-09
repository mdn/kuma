from nose.tools import eq_, ok_

from sumo.tests import TestCase
from wiki.forms import RevisionForm, RevisionValidationForm
from wiki.tests import doc_rev, normalize_html


class FormSectionEditingTests(TestCase):
    fixtures = ['test_users.json']

    def test_form_loaded_with_section(self):
        """RevisionForm given section_id should load initial content for only
        one section"""
        d, r = doc_rev("""
            <h1 id="s1">s1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">s2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """)
        expected = """
            <h1 id="s2">s2</h1>
            <p>test</p>
            <p>test</p>
        """
        rev_form = RevisionForm(instance=r, section_id="s2")
        eq_(normalize_html(expected),
            normalize_html(rev_form.initial['content']))

    def test_form_save_section(self):
        d, r = doc_rev("""
            <h1 id="s1">s1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">s2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """)
        replace_content = """
            <h1 id="s2">New stuff</h1>
            <p>new stuff</p>
        """
        expected = """
            <h1 id="s1">s1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">New stuff</h1>
            <p>new stuff</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """
        rev_form = RevisionForm({"content": replace_content},
                                instance=r,
                                section_id="s2")
        new_rev = rev_form.save(r.creator, d)
        eq_(normalize_html(expected),
            normalize_html(new_rev.content))


class RevisionValidationTests(TestCase):
    fixtures = ['test_users.json']

    def test_form_rejects_empty_slugs_with_parent(self):
        """RevisionValidationForm should reject empty slugs, even if there
        is a parent slug portion"""
        data = {'parent_slug': 'User:groovecoder',
                'slug': '', 'title': 'Title', 'content': 'Content'}
        rev_form = RevisionValidationForm(data)
        rev_form.parent_slug = 'User:groovecoder'
        ok_(not rev_form.is_valid())
