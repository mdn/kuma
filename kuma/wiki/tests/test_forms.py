from django.test import RequestFactory

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from kuma.users.tests import UserTestCase

from ..forms import RevisionForm, TreeMoveForm
from ..tests import normalize_html, revision


class FormEditorSafetyFilterTests(UserTestCase):

    @attr('bug821986')
    def test_form_onload_attr_filter(self):
        """RevisionForm should strip out any harmful onload attributes from
        input markup"""
        rev = revision(save=True, is_approved=True, content="""
            <svg><circle onload=confirm(3)>
        """)
        rev_form = RevisionForm(instance=rev)
        ok_('onload' not in rev_form.initial['content'])


class RevisionFormTests(UserTestCase):

    def test_form_loaded_with_section(self):
        """RevisionForm given section_id should load initial content for only
        one section"""
        rev = revision(save=True, is_approved=True, content="""
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
        rev_form = RevisionForm(instance=rev, section_id="s2")
        eq_(normalize_html(expected),
            normalize_html(rev_form.initial['content']))

    def test_form_save_section(self):
        rev = revision(save=True, is_approved=True, content="""
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
                                instance=rev,
                                section_id="s2")
        request = RequestFactory().get('/')
        request.user = rev.creator
        new_rev = rev_form.save(request, rev.document)
        eq_(normalize_html(expected),
            normalize_html(new_rev.content))

    def test_form_rejects_empty_slugs_with_parent(self):
        """
        RevisionForm should reject empty slugs, even if there
        is a parent slug portion
        """
        data = {
            'slug': '',
            'title': 'Title',
            'content': 'Content',
        }
        rev_form = RevisionForm(data, parent_slug='User:groovecoder')
        ok_(not rev_form.is_valid())

    def test_case_sensitive_tags(self):
        """
        RevisionForm should reject new tags that are the same as existing tags
        that only differ by case.
        """
        rev = revision(save=True, tags='JavaScript')
        data = {
            'content': 'Content',
            'toc_depth': 1,
            'tags': 'Javascript',  # Note the lower-case "S".
        }
        rev_form = RevisionForm(data, instance=rev)
        ok_(not rev_form.is_valid())
        ok_('use these tag(s) instead' in rev_form.errors['tags'][0])


class TreeMoveFormTests(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_form_properly_strips_leading_cruft(self):
        """
        Tests that leading slash, trailing slash, and {locale}/docs/
        are removed if included
        """
        comparisons = [
            ['/somedoc', 'somedoc'],  # leading slash
            ['/en-US/docs/mynewplace', 'mynewplace'],  # locale and docs
            ['/docs/one', 'one'],  # leading docs
            ['docs/one', 'one'],  # leading docs without slash
            ['fr/docs/one', 'one'],  # foreign locale with docs
            ['docs/article-title/docs', 'article-title/docs'],  # docs with later docs
            ['/en-US/docs/something/', 'something']  # trailing slash
        ]

        for comparison in comparisons:
            form = TreeMoveForm({'locale': 'en-US', 'title': 'Article',
                                 'slug': comparison[0]})
            form.is_valid()
            eq_(comparison[1], form.cleaned_data['slug'])

    def test_form_enforces_parent_doc_to_exist(self):
        form = TreeMoveForm({'locale': 'en-US', 'title': 'Article',
                             'slug': 'nothing/article'})
        form.is_valid()
        ok_(form.errors)
        ok_(u'Parent' in form.errors.as_text())
        ok_(u'does not exist' in form.errors.as_text())
