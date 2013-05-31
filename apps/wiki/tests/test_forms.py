from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from sumo.tests import TestCase
from wiki.forms import RevisionForm, RevisionValidationForm
from wiki.tests import doc_rev, normalize_html


class FormEditorSafetyFilterTests(TestCase):
    fixtures = ['test_users.json']

    @attr('bug821986')
    def test_form_onload_attr_filter(self):
        """RevisionForm should strip out any harmful onload attributes from
        input markup"""
        d, r = doc_rev("""
            <svg><circle onload=confirm(3)>
        """)
        rev_form = RevisionForm(instance=r)
        ok_('onload' not in rev_form.initial['content'])
        
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
