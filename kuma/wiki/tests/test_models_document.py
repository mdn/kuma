# -*- coding: utf-8 -*-
"""
Tests for kuma.wiki.models.Document.

Legacy tests are in kuma/wiki/tests/test_models.py
"""
from __future__ import unicode_literals

import json
from datetime import timedelta

import mock
import pytest

from . import normalize_html
from ..models import Document, Revision


@pytest.fixture
def doc_with_sections(root_doc, wiki_user):
    src = """
    <h2 id="First">First</h2>
    <p>This is a document</p>

    <section id="Quick_Links" class="Quick_Links">
      <ol>
        <li><a href="%(root_url)s">Existing link</a></li>
        <li><a href="/en-US/docs/NewPage">New link</a></li>
      </ol>
    </section>

    <h3 id="Subnav">Subnav</h3>
    <p>Subnav:</p>
    <ul>
      <li><a href="%(root_url)s">Existing link</a></li>
      <li><a href="/en-US/docs/NewPage">New link</a></li>
    </ul>

    <h2>Second</h2>
    <p>Another section, with an
      <a href="%(root_url)s">existing link</a> and a
      <a href="/en-US/docs/NewPage">new link</a>.</p>

    <h2 id="Short">Short</h2>
    <p>This is the short section.</p>
    """ % {'root_url': root_doc.get_absolute_url()}
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, content=src, creator=wiki_user)
    root_doc.save()
    return root_doc


def test_get_json_data_cached_parsed_json(root_doc):
    """
    Document.get_json_data uses cached parsed JSON from previous calls.

    TODO: Is this a good idea? It seems like it should never run
    (callers should work to run it once if efficency is needed), and
    if it does run twice, would hide any changes made to the instance.
    """
    stale_data = {"stale": "like an old crouton"}
    root_doc._json_data = stale_data
    assert root_doc.get_json_data() == stale_data


def test_get_json_data_cached_db_json(root_doc):
    """Document.get_json_data uses cached JSON stored in DB."""
    root_doc.json = '{"stale": "ready for fondue"}'
    expected = {'stale': 'ready for fondue'}
    assert root_doc.get_json_data() == expected


@mock.patch.object(Document, 'build_json_data')
def test_get_json_data_ignores_bad_cached_db_json(mocked_build, root_doc):
    """Document.get_json_data ignores bad cached JSON stored in DB."""
    root_doc.json = 'I am invalid'
    fresh = {'fresh': 'baked this morning'}
    mocked_build.return_value = fresh
    assert root_doc.get_json_data() == fresh


@mock.patch.object(Document, 'build_json_data')
def test_get_json_data_detects_stale_cached_db_json(mocked_build, root_doc):
    """Document.get_json_data will rebuild stale cached JSON if requested."""
    old_mod = root_doc.modified - timedelta(seconds=1)
    root_doc.json = '{"json_modified": "%s"}' % old_mod.isoformat()
    fresh = {'fresh': 'still hot'}
    mocked_build.return_value = fresh
    assert root_doc.get_json_data(stale=False) == fresh


@mock.patch.object(Document, 'build_json_data')
def test_get_json_data_keeps_cached_db_json(mocked_build, root_doc):
    """Document.get_json_data does not rebuild fresh cached JSON."""
    newer_mod = root_doc.modified + timedelta(seconds=1)
    newer_json = {"json_modified": newer_mod.isoformat()}
    root_doc.json = json.dumps(newer_json)
    mocked_build.side_effect = Exception("Should not be called.")
    assert root_doc.get_json_data(stale=False) == newer_json


@mock.patch.object(Document, 'build_json_data')
def test_get_json_data_maintenance(mocked_build, root_doc, settings):
    """The JSON data is not cached in read-only maintenance mode."""
    settings.MAINTENANCE_MODE = True
    mm_json = {'mode': 'MM'}
    mocked_build.return_value = mm_json
    assert root_doc.get_json_data() == mm_json
    root_doc.refresh_from_db()
    assert root_doc.json is None


def test_build_json_data_unsaved_doc():
    """
    An unsaved doc can generate some JSON.

    TODO: Maybe this should return something empty, so it will get regenerated
    after saving. It is not used in the new document process, and only test
    code appears to exercise this branch.
    """
    doc = Document(
        slug='NewDoc',
        title='New Doc',
        uuid='765203ea-c5b8-4385-a551-26c1ef9fc843'
    )
    new_json = doc.build_json_data()
    now_iso = new_json['json_modified']
    expected = {
        'id': None,
        'json_modified': now_iso,
        'label': 'New Doc',
        'last_edit': '',
        'locale': 'en-US',
        'localization_tags': [],
        'modified': now_iso,
        'review_tags': [],
        'sections': [],
        'slug': 'NewDoc',
        'summary': '',
        'tags': [],
        'title': 'New Doc',
        'translations': [],
        'url': u'/en-US/docs/NewDoc',
        'uuid': '765203ea-c5b8-4385-a551-26c1ef9fc843'
    }
    assert new_json == expected


def test_build_json_data_with_translations(trans_doc):
    """A document's JSON includes translations."""
    en_doc = trans_doc.parent
    en_json = en_doc.build_json_data()
    en_expected = {
        'id': en_doc.id,
        'json_modified': en_json['json_modified'],
        'label': 'Root Document',
        'last_edit': '2017-04-14T12:15:00',
        'locale': 'en-US',
        'localization_tags': [],
        'modified': en_doc.modified.isoformat(),
        'review_tags': [],
        'sections': [],
        'slug': 'Root',
        'summary': 'Getting started...',
        'tags': [],
        'title': 'Root Document',
        'translations': [
            {
                'last_edit': '2017-04-14T12:20:00',
                'locale': 'fr',
                'localization_tags': [],
                'review_tags': [],
                'summary': 'Mise en route...',
                'tags': [],
                'title': 'Racine du Document',
                'url': '/fr/docs/Racine',
                'uuid': str(trans_doc.uuid),
            }
        ],
        'url': '/en-US/docs/Root',
        'uuid': str(en_doc.uuid),
    }
    assert en_json == en_expected

    fr_json = trans_doc.build_json_data()
    fr_expected = {
        'id': trans_doc.id,
        'json_modified': fr_json['json_modified'],
        'label': 'Racine du Document',
        'last_edit': '2017-04-14T12:20:00',
        'locale': 'fr',
        'localization_tags': [],
        'modified': trans_doc.modified.isoformat(),
        'review_tags': [],
        'sections': [],
        'slug': 'Racine',
        'summary': 'Mise en route...',
        'tags': [],
        'title': 'Racine du Document',
        'translations': [
            {
                'last_edit': '2017-04-14T12:15:00',
                'locale': 'en-US',
                'localization_tags': [],
                'review_tags': [],
                'summary': 'Getting started...',
                'tags': [],
                'title': 'Root Document',
                'url': '/en-US/docs/Root',
                'uuid': str(en_doc.uuid),
            }
        ],
        'url': '/fr/docs/Racine',
        'uuid': str(trans_doc.uuid),
    }
    assert fr_json == fr_expected


def test_build_json_data_with_tags(trans_doc):
    """Document JSON includes lists of tags."""
    en_doc = trans_doc.parent
    en_doc.tags.add("NeedsUpdate", "Beginner")
    en_doc.current_revision.localization_tags.add('english_already')
    en_doc.current_revision.review_tags.add('technical')
    trans_doc.tags.add("NeedsUpdate", "Débutant")
    trans_doc.current_revision.localization_tags.add('inprogress')
    trans_doc.current_revision.review_tags.add('editorial')

    en_json = en_doc.build_json_data()
    assert sorted(en_json['tags']) == ['Beginner', 'NeedsUpdate']
    assert en_json['localization_tags'] == ['english_already']
    assert en_json['review_tags'] == ['technical']
    fr_json = en_json['translations'][0]
    assert sorted(fr_json['tags']) == ["Débutant", "NeedsUpdate"]
    assert fr_json['localization_tags'] == ['inprogress']


def test_build_json_data_with_summary(trans_doc):
    """The summary is the cached HTML SEO description."""
    en_doc = trans_doc.parent
    en_doc.summary_html = 'Cached Summary'
    en_doc.save()
    en_json = en_doc.build_json_data()
    assert en_json['summary'] == 'Cached Summary'
    assert en_json['translations'][0]['summary'] == 'Mise en route...'


def test_build_json_data_uses_rendered_html(root_doc):
    """
    build_json_data uses rendered HTML when available.

    re bug 982174: Macro-generated sections do not appear in JSON
    """
    root_doc.html = """
    <h2>Section 1</h2>
    <p>Foo</p>
    {{ h2_macro('Section 2') }}
    <p>Bar</p>
    <h2>Section 3</h2>
    <p>Foo</p>
    """
    root_doc.save()
    json_data = root_doc.build_json_data()
    expected_sections = [
        {'id': 'Section_1', 'title': 'Section 1'},
        {'id': 'Section_3', 'title': 'Section 3'}
    ]
    assert json_data['sections'] == expected_sections

    root_doc.rendered_html = root_doc.html.replace(
        "{{ h2_macro('Section 2') }}",
        "<h2>Section 2</h2>\n<p>I'm generated by KumaScript</p>")
    root_doc.save()
    json_data = root_doc.build_json_data()
    expected_sections = [
        {'id': 'Section_1', 'title': 'Section 1'},
        {'id': 'Section_2', 'title': 'Section 2'},
        {'id': 'Section_3', 'title': 'Section 3'}
    ]
    assert json_data['sections'] == expected_sections


def test_nearest_zone(doc_hierarchy_with_zones, cleared_cacheback_cache):
    """
    Test the nearest zone property of English and non-English documents.
    """
    top_doc = doc_hierarchy_with_zones.top
    top_zone = top_doc.zone

    fr_top_doc = top_doc.translations.get(locale='fr')
    de_top_doc = top_doc.translations.get(locale='de')

    assert fr_top_doc.parent == top_doc
    assert de_top_doc.parent == top_doc
    assert top_doc.nearest_zone == top_zone
    # The French translation of the top doc doesn't have its own locale-
    # specific nearest zone, so it'll return the nearest zone of its parent.
    assert fr_top_doc.nearest_zone == top_doc.nearest_zone
    # The German translation of the top doc does have its own
    # locale-specific nearest zone.
    assert de_top_doc.nearest_zone == de_top_doc.zone


def test_nearest_zone_when_no_parent(doc_hierarchy_with_zones,
                                     cleared_cacheback_cache):
    """
    Silly end-case test of the nearest-zone property of a non-English document
    without a parent.
    """
    top_doc = doc_hierarchy_with_zones.top
    fr_top_doc = top_doc.translations.get(locale='fr')
    fr_top_doc.parent = None
    fr_top_doc.save()

    assert not fr_top_doc.nearest_zone


@pytest.mark.parametrize('doc_name,expected_result', [
    ('top', True),
    ('bottom', False),
    ('de', True),
    ('fr', True),
    ('root', False),
])
def test_is_zone_root(doc_hierarchy_with_zones, root_doc,
                      cleared_cacheback_cache, doc_name, expected_result):
    """
    Test is_zone_root.
    """
    if doc_name == 'root':
        doc = root_doc
    elif doc_name in ('de', 'fr'):
        doc = doc_hierarchy_with_zones.top.translations.get(locale=doc_name)
    else:
        doc = getattr(doc_hierarchy_with_zones, doc_name)
    assert doc.is_zone_root is expected_result


def test_get_section_content(doc_with_sections):
    """A section can be extracted by ID."""
    result = doc_with_sections.get_section_content('Short')
    expected = "<p>This is the short section.</p>"
    assert normalize_html(result) == normalize_html(expected)


def test_get_body_html(doc_with_sections):
    """The quick_links and subnav are removed from the body HTML."""
    result = doc_with_sections.get_body_html()
    expected = """
    <h2 id="First">First</h2>
    <p>This is a document</p>
    <h2 id="Second">Second</h2>
    <p>Another section, with an
      <a href="/en-US/docs/Root">existing link</a> and a
      <a class="new" rel="nofollow" href="/en-US/docs/NewPage">new link</a>.
    </p>
    <h2 id="Short">Short</h2>
    <p>This is the short section.</p>
    """
    assert normalize_html(result) == normalize_html(expected)


def test_get_quick_links_html(doc_with_sections):
    """The quick_links HTML can be extracted from the revision."""
    result = doc_with_sections.get_quick_links_html()
    expected = """
    <ol>
      <li><a href="/en-US/docs/Root">Existing link</a></li>
      <li><a class="new" rel="nofollow" href="/en-US/docs/NewPage">New link</a></li>
    </ol>
    """
    assert normalize_html(result) == normalize_html(expected)


def test_get_zone_subnav_local_html(doc_with_sections):
    """The zone subnav local HTML can be extracted from the revision."""
    result = doc_with_sections.get_zone_subnav_local_html()
    expected = """
    <p>Subnav:</p>
    <ul>
      <li><a href="/en-US/docs/Root">Existing link</a></li>
      <li><a class="new" rel="nofollow" href="/en-US/docs/NewPage">New link</a></li>
    </ul>
    """
    assert normalize_html(result) == normalize_html(expected)
