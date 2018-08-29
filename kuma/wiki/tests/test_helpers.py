# -*- coding: utf-8 -*-
import mock
import pytest

from django.contrib.sites.models import Site
from django.template import TemplateDoesNotExist
from pyquery import PyQuery as pq

from kuma.users.tests import UserTestCase

from . import document, revision, WikiTestCase
from ..templatetags.jinja_helpers import (absolutify,
                                          include_svg,
                                          revisions_unified_diff,
                                          selector_content_find, tojson,
                                          wiki_url)


class HelpTests(WikiTestCase):

    def test_tojson(self):
        assert (tojson({'title': '<script>alert("Hi!")</script>'}) ==
                '{"title": "&lt;script&gt;alert(&quot;Hi!&quot;)&lt;/script&gt;"}')

    @mock.patch.object(Site.objects, 'get_current')
    def test_absolutify(self, get_current):
        get_current.return_value.domain = 'testserver'

        assert absolutify('') == 'https://testserver/'
        assert absolutify('/') == 'https://testserver/'
        assert absolutify('//') == 'https://testserver/'
        assert absolutify('/foo/bar') == 'https://testserver/foo/bar'
        assert absolutify('http://domain.com') == 'http://domain.com'

        site = Site(domain='otherserver')
        assert absolutify('/woo', site) == 'https://otherserver/woo'

        assert absolutify('/woo?var=value') == 'https://testserver/woo?var=value'
        assert (absolutify('/woo?var=value#fragment') ==
                'https://testserver/woo?var=value#fragment')


def test_include_svg_invalid_path():
    """An invalid SVG path raises an exception."""
    with pytest.raises(TemplateDoesNotExist):
        include_svg('invalid.svg')


def test_include_svg_no_title():
    """If the title is not given, the SVG title is not changed."""
    no_title = include_svg('includes/icons/social/twitter.svg')
    svg = pq(no_title, namespaces={'svg': 'http://www.w3.org/2000/svg'})
    svg_title = svg('svg|title')
    assert svg_title.text() == 'Twitter'


@pytest.mark.parametrize('title', ('New Title', u'Nuevo Título'))
def test_include_svg_replace_title(title):
    """The SVG title can be replaced."""
    new_title = include_svg('includes/icons/social/twitter.svg', title)
    svg = pq(new_title, namespaces={'svg': 'http://www.w3.org/2000/svg'})
    svg_title = svg('svg|title')
    assert svg_title.text() == title


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
