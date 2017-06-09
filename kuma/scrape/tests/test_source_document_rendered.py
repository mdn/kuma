# -*- coding: utf-8 -*-
"""Tests for the DocumentRenderedSource class (GET document)."""
from __future__ import unicode_literals
from datetime import datetime

import pytest

from kuma.scrape.sources import DocumentRenderedSource
from kuma.wiki.models import Document, DocumentZone, Revision
from . import mock_requester, mock_storage


@pytest.fixture
def zone_root_doc(root_doc, settings):
    """A Document record with a DocumentZone with style and a redirect."""
    settings.PIPELINE_CSS['zone-special'] = {
        'output_filename': 'build/styles/zone-special.css'}
    doc = Document.objects.create(
        locale='en-US',
        slug=root_doc.slug + '/Zone',
        parent_topic=root_doc)
    DocumentZone.objects.create(
        document=doc,
        url_root='Zone',
        css_slug='special')
    revision = Revision.objects.create(
        document=doc,
        creator=root_doc.current_revision.creator,
        content='<p>This is the Zone.</p>',
        created=datetime(2016, 12, 14))
    assert doc.current_revision == revision
    doc.rendered_html = doc.current_revision.content
    doc.save()
    return doc


@pytest.fixture
def zone_child_doc(zone_root_doc):
    """A Document record that is below the zone root."""
    doc = Document.objects.create(
        locale='en-US',
        slug=zone_root_doc.slug + '/Child',
        parent_topic=zone_root_doc)
    creator = zone_root_doc.current_revision.creator
    Revision.objects.create(
        content='<p>A zone subpage.</p>',
        creator=creator,
        document=doc)
    return doc


def test_root_doc(root_doc, client):
    """Test a page without redirects."""
    url = root_doc.get_absolute_url()
    html = client.get(url).content
    source = DocumentRenderedSource(url)
    requester = mock_requester(content=html)
    storage = mock_storage(spec=['save_document_rendered'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    storage.save_document_rendered.assert_called_once_with(
        'en-US', 'Root', {})


def test_non_zone_redirect(root_doc, client):
    """
    Test a page with non-zone redirects.

    For example, a page might redirect from http:// to https:// without
    changing the path.
    """
    url = root_doc.get_absolute_url()
    html = client.get(url).content
    source = DocumentRenderedSource(url)
    requester = mock_requester(
        response_spec=['content', 'history', 'status_code', 'url'],
        history=[(301, url)],
        final_path=url,
        content=html)
    storage = mock_storage(spec=['save_document_rendered'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    storage.save_document_rendered.assert_called_once_with(
        'en-US', 'Root', {})


def test_zone_root_doc(zone_root_doc, client):
    """The zone_css_slug is extracted from zone roots."""
    url = zone_root_doc.get_absolute_url()
    html = client.get(url, follow=True).content
    source = DocumentRenderedSource(url)
    requester = mock_requester(
        response_spec=['content', 'history', 'status_code', 'url'],
        history=[(302, url)],
        final_path=zone_root_doc.zone.url_root,
        content=html)
    storage = mock_storage(spec=['save_document_rendered'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    context = {
        'redirect_to': 'Zone',
        'is_zone_root': True,
        'zone_css_slug': 'special'}
    storage.save_document_rendered.assert_called_once_with(
        'en-US', 'Root/Zone', context)


def test_zone_child_doc(zone_root_doc, zone_child_doc, client):
    """The zone_css_slug is not extracted from zone children."""
    url = zone_child_doc.get_absolute_url()
    html = client.get(url, follow=True).content
    source = DocumentRenderedSource(url)
    requester = mock_requester(
        response_spec=['content', 'history', 'status_code', 'url'],
        history=[(302, url)],
        final_path=zone_root_doc.zone.url_root,
        content=html)
    storage = mock_storage(spec=['save_document_rendered'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    context = {'redirect_to': 'Zone'}
    storage.save_document_rendered.assert_called_once_with(
        'en-US', 'Root/Zone/Child', context)


def test_missing_doc(client):
    """
    A missing document results in an error.

    One cause: translations are requested, and a recently deleted
    translation is in the metadata.
    """
    source = DocumentRenderedSource('/en-US/docs/missing')
    requester = mock_requester(status_code=404)
    storage = mock_storage()
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
