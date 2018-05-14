# -*- coding: utf-8 -*-
import mock
import pytest

from django.contrib.sites.models import Site

from kuma.core.cache import memcache
from kuma.core.tests import eq_
from kuma.users.tests import UserTestCase

from . import document, revision, WikiTestCase
from ..models import DocumentZone
from ..templatetags.jinja_helpers import (absolutify,
                                          document_zone_management_links,
                                          revisions_unified_diff,
                                          selector_content_find, tojson,
                                          wiki_url)


class HelpTests(WikiTestCase):

    def test_tojson(self):
        eq_(tojson({'title': '<script>alert("Hi!")</script>'}),
            '{"title": "&lt;script&gt;alert(&quot;Hi!&quot;)&lt;/script&gt;"}')

    @mock.patch.object(Site.objects, 'get_current')
    def test_absolutify(self, get_current):
        get_current.return_value.domain = 'testserver'

        eq_(absolutify(''), 'https://testserver/')
        eq_(absolutify('/'), 'https://testserver/')
        eq_(absolutify('//'), 'https://testserver/')
        eq_(absolutify('/foo/bar'), 'https://testserver/foo/bar')
        eq_(absolutify('http://domain.com'), 'http://domain.com')

        site = Site(domain='otherserver')
        eq_(absolutify('/woo', site), 'https://otherserver/woo')

        eq_(absolutify('/woo?var=value'), 'https://testserver/woo?var=value')
        eq_(absolutify('/woo?var=value#fragment'),
            'https://testserver/woo?var=value#fragment')


class RevisionsUnifiedDiffTests(UserTestCase, WikiTestCase):

    def test_from_revision_none(self):
        rev = revision()
        diff = revisions_unified_diff(None, rev)  # No AttributeError
        assert diff == "Diff is unavailable."

    def test_from_revision_non_ascii(self):
        doc1 = document(title=u'Gänsefüßchen', save=True)
        rev1 = revision(document=doc1, content=u'spam', save=True)
        doc2 = document(title=u'Außendienstüberwachlösung', save=True)
        rev2 = revision(document=doc2, content=u'eggs', save=True)
        revisions_unified_diff(rev1, rev2)  # No UnicodeEncodeError


class DocumentZoneTests(UserTestCase, WikiTestCase):
    """Tests for DocumentZone helpers"""

    def setUp(self):
        super(DocumentZoneTests, self).setUp()

        self.root_links_content = """
            <p>Links content</p>
        """
        self.root_content = """
            <h4 id="links">Links</h4>
            %s
        """ % (self.root_links_content)

        root_rev = revision(title='ZoneRoot',
                            slug='ZoneRoot',
                            content=self.root_content,
                            is_approved=True,
                            save=True)
        self.root_doc = root_rev.document
        self.root_doc.rendered_html = self.root_content
        self.root_doc.save()

        self.root_zone = DocumentZone(document=self.root_doc)
        self.root_zone.save()

        sub_rev = revision(title='SubPage',
                           slug='SubPage',
                           content='This is a subpage',
                           is_approved=True,
                           save=True)
        self.sub_doc = sub_rev.document
        self.sub_doc.parent_topic = self.root_doc
        self.sub_doc.rendered_html = sub_rev.content
        self.sub_doc.save()

        self.sub_sub_links_content = """
            <p>Sub-page links content</p>
        """
        self.sub_sub_content = """
            <h4 id="links">Links</h4>
            %s
        """ % (self.sub_sub_links_content)

        sub_sub_rev = revision(title='SubSubPage',
                               slug='SubSubPage',
                               content='This is a subpage',
                               is_approved=True,
                               save=True)
        self.sub_sub_doc = sub_sub_rev.document
        self.sub_sub_doc.parent_topic = self.sub_doc
        self.sub_sub_doc.rendered_html = self.sub_sub_content
        self.sub_sub_doc.save()

        other_rev = revision(title='otherPage',
                             slug='otherPage',
                             content='This is an other page',
                             is_approved=True,
                             save=True)
        self.other_doc = other_rev.document
        self.other_doc.save()
        memcache.clear()

    def test_document_zone_links(self):
        admin = self.user_model.objects.filter(is_superuser=True)[0]
        random = self.user_model.objects.filter(is_superuser=False)[0]
        cases = [
            (admin, self.root_doc, False, True),
            (random, self.root_doc, False, False),
            (admin, self.sub_doc, True, True),
            (random, self.sub_doc, False, False),
            (admin, self.other_doc, True, False),
            (random, self.other_doc, False, False),
        ]
        for (user, doc, add, change) in cases:
            result_links = document_zone_management_links(user, doc)
            eq_(add, result_links['add'] is not None, (user, doc))
            eq_(change, result_links['change'] is not None)


class SelectorContentFindTests(UserTestCase, WikiTestCase):
    def test_selector_not_found_returns_empty_string(self):
        doc_content = u'<div id="not-summary">Not the summary</div>'
        doc1 = document(title=u'Test Missing Selector', save=True)
        doc1.rendered_html = doc_content
        doc1.save()
        revision(document=doc1, content=doc_content, save=True)
        content = selector_content_find(doc1, 'summary')
        assert content == ''

    def test_pyquery_bad_selector_syntax_returns_empty_string(self):
        doc_content = u'<div id="not-suNot the summary</span'
        doc1 = document(title=u'Test Missing Selector', save=True)
        doc1.rendered_html = doc_content
        doc1.save()
        revision(document=doc1, content=doc_content, save=True)
        content = selector_content_find(doc1, '.')
        assert content == ''


@pytest.mark.parametrize(
    "path, expected", (
        ('MDN/Getting_started', '/en-US/docs/MDN/Getting_started'),
        ('MDN/Getting_started#Option_1_I_like_words',
         '/en-US/docs/MDN/Getting_started#Option_1_I_like_words'),
    ), ids=('simple', 'fragment'))
def test_wiki_url(path, expected):
    """Test wiki_url, without client languages."""
    out = wiki_url(path)
    assert out == expected
