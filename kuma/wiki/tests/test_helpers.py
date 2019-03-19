# -*- coding: utf-8 -*-
from datetime import datetime

import pytest
from django.template import TemplateDoesNotExist
from pyquery import PyQuery as pq

from ..models import Document, Revision
from ..templatetags.jinja_helpers import (absolutify,
                                          include_svg,
                                          revisions_unified_diff,
                                          selector_content_find, tojson,
                                          wiki_url)


def test_tojson():
    """tojson converts dicts to JSON objects with escaping."""
    output = tojson({'title': '<script>alert("Hi!")</script>'})
    expected = ('{"title": "&lt;script&gt;alert(&quot;Hi!&quot;)'
                '&lt;/script&gt;"}')
    assert output == expected


@pytest.mark.parametrize(
    'path,abspath',
    (('', 'https://testserver/'),
     ('/', 'https://testserver/'),
     ('//', 'https://testserver/'),
     ('/foo/bar', 'https://testserver/foo/bar'),
     ('http://domain.com', 'http://domain.com'),
     ('/woo?var=value', 'https://testserver/woo?var=value'),
     ('/woo?var=value#fragment', 'https://testserver/woo?var=value#fragment'),
     ))
def test_absolutify(settings, path, abspath):
    """absolutify adds the current site to paths without domains."""
    settings.SITE_URL = 'https://testserver'
    assert absolutify(path) == abspath


def test_absolutify_dev(settings):
    """absolutify uses http in development."""
    settings.SITE_URL = 'http://localhost:8000'
    assert absolutify('') == 'http://localhost:8000/'


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


def test_include_svg_add_title_title_id():
    """The SVG title and id attribute can be added."""
    title, title_id = 'New Title', 'title-id'
    new_svg = include_svg('includes/icons/social/twitter.svg', title, title_id)
    new_svg = pq(new_svg, namespaces={'svg': 'http://www.w3.org/2000/svg'})
    svg_title = new_svg('svg|title')
    svg_title_id = new_svg('svg|title').attr['id']
    assert svg_title.text() == title
    assert svg_title_id == title_id


def test_revisions_unified_diff_none(root_doc):
    """Passing a None revision does not raise an AttributeError."""
    diff = revisions_unified_diff(None, root_doc.current_revision)
    assert diff == "Diff is unavailable."


def test_revisions_unified_diff_non_ascii(wiki_user):
    """Documents with non-ASCII titles do not have Unicode errors in diffs."""
    title1 = u'Gänsefüßchen'
    doc1 = Document.objects.create(
        locale='en-US', slug=title1, title=title1)
    rev1 = Revision.objects.create(
        document=doc1,
        creator=wiki_user,
        content=u'<p>%s started...</p>' % title1,
        title=title1,
        created=datetime(2018, 11, 21, 18, 39))

    title2 = u'Außendienstüberwachlösung'
    doc2 = Document.objects.create(
        locale='en-US', slug=title2, title=title2)
    rev2 = Revision.objects.create(
        document=doc2,
        creator=wiki_user,
        content=u'<p>%s started...</p>' % title2,
        title=title1,
        created=datetime(2018, 11, 21, 18, 41))

    revisions_unified_diff(rev1, rev2)  # No UnicodeEncodeError


def test_selector_content_find_not_found_returns_empty_string(root_doc):
    """When the ID is not in the content, return an empty string."""
    root_doc.rendered_html = root_doc.current_revision.content
    content = selector_content_find(root_doc, 'summary')
    assert content == ''


def test_selector_content_find_bad_selector_returns_empty_string(root_doc):
    """When the ID is invalid, return an empty string."""
    root_doc.rendered_html = root_doc.current_revision.content
    content = selector_content_find(root_doc, '.')
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
