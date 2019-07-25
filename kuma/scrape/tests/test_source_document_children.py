# -*- coding: utf-8 -*-
"""Tests for the DocumentChildrenSource class ($children API)."""
from __future__ import unicode_literals

from . import mock_requester, mock_storage
from ..sources import DocumentChildrenSource

# Partial data from
# https://wiki.developer.mozilla.org/en-US/docs/Web/Guide/HTML/HTML5$children
child_data = {
    'locale': 'en-US',
    'slug': 'Web/Guide/HTML/HTML5',
    'subpages': [
        {
            # Full child data
            'locale': 'en-US',
            'slug': 'Web/Guide/HTML/HTML5/Validation',
            'subpages': [],
            'title': 'Constraint validation',
            'url': '/en-US/docs/Web/Guide/HTML/HTML5/Validation'
        }, {
            # Minimum data actually used
            'url': '/en-US/docs/Web/Guide/HTML/HTML5/Parser',
        }
    ],
    'title': 'HTML5',
    'url': '/en-US/docs/Web/Guide/HTML/HTML5'
}


def test_extract_no_subpages():
    """If a document has no subpages, none are extracted."""
    data = child_data.copy()
    data['subpages'] = []
    children = DocumentChildrenSource(data['url']).extract_data(data)
    assert children == []


def test_gather_with_subpages():
    """Document Subpages are returned as new resources to fetch."""
    source = DocumentChildrenSource(child_data['url'])
    requester = mock_requester(response_spec=['json'], json=child_data)
    storage = mock_storage(['get_document_children', 'save_document_children'])
    resources = source.gather(requester, storage)
    assert resources == [
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Validation', {}),
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Parser', {}),
    ]
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    storage.get_document_children.assert_called_once_with(
        'en-US', 'Web/Guide/HTML/HTML5')
    storage.save_document_children.assert_called_once_with(
        'en-US', 'Web/Guide/HTML/HTML5', child_data)


def test_gather_existing():
    source = DocumentChildrenSource(child_data['url'])
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(['get_document_children', 'save_document_children'])
    storage.get_document_children.return_value = child_data
    resources = source.gather(requester, storage)
    assert resources == [
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Validation', {}),
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Parser', {}),
    ]
    storage.get_document_children.assert_called_once_with(
        'en-US', 'Web/Guide/HTML/HTML5')
    assert not storage.save_document_children.called


def test_depth_all():
    """depth=all is propagated to child pages."""
    opts = {'depth': 'all'}
    source = DocumentChildrenSource(child_data['url'], **opts)
    children = source.extract_data(child_data)
    assert children == [
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Validation', opts),
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Parser', opts),
    ]


def test_depth_decreases():
    """depth=n is propagated as depth=n-1 to child pages."""
    source_opts = {'depth': 3, 'translations': True}
    source = DocumentChildrenSource(child_data['url'], **source_opts)
    children = source.extract_data(child_data)
    opts = {'depth': 2, 'translations': True}
    assert children == [
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Validation', opts),
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Parser', opts),
    ]


def test_final_depth():
    """depth=1 is not propagated to child pages."""
    source_opts = {'depth': 1, 'revisions': 3}
    source = DocumentChildrenSource(child_data['url'], **source_opts)
    children = source.extract_data(child_data)
    opts = {'revisions': 3}
    assert children == [
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Validation', opts),
        ('document', '/en-US/docs/Web/Guide/HTML/HTML5/Parser', opts),
    ]
