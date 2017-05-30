# -*- coding: utf-8 -*-
"""Tests for the ZoneRootSource class (zone redirect URL)."""
from __future__ import unicode_literals

import pytest

from kuma.scrape.sources import ZoneRootSource
from . import mock_requester, mock_storage


def test_escaped_url():
    """Detect URL-encoded paths and fail at init."""
    with pytest.raises(ValueError) as error:
        ZoneRootSource('/tr/docs/%C3%96%C4%9Fren/CSS')
    expected_message = 'URL-encoded path "/tr/docs/%C3%96%C4%9Fren/CSS"'
    assert str(error.value) == expected_message


def test_invalid_url():
    """Detect invalid paths and fail at init."""
    source = ZoneRootSource('/en-US')
    assert source.state == source.STATE_ERROR


def test_gather():
    """Zone root data can be gathered from metadata on the first pass."""
    metadata = {
        'url': '/en-US/docs/Root/Zone',
        'locale': 'en-US'
    }
    source = ZoneRootSource('/en-US/Zone')
    requester = mock_requester(response_spec=['json'], json=metadata)
    storage = mock_storage(spec=['get_zone_root', 'save_zone_root'])
    resources = source.gather(requester, storage)
    assert resources == [('document', '/en-US/docs/Root/Zone', {})]
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    data = {
        'doc_path': '/en-US/docs/Root/Zone',
        'zone_path': '/en-US/Zone',
    }
    storage.save_zone_root.assert_called_once_with('/en-US/Zone', data)


def test_gather_when_stored():
    """Previously stored zone root data prevents scraping."""
    data = {
        'doc_path': '/en-US/docs/Root/Zone',
        'zone_path': '/en-US/Zone',
    }
    source = ZoneRootSource('/en-US/Zone')
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=['get_zone_root'])
    storage.get_zone_root.return_value = data
    resources = source.gather(requester, storage)
    assert resources == [('document', '/en-US/docs/Root/Zone', {})]
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_NO


def test_gather_notzone_is_error():
    """Passing a non-zone URL is detected when processing metadata."""
    metadata = {
        'url': '/en-US/docs/Root/Zone',
        'locale': 'en-US'
    }
    source = ZoneRootSource('/en-US/docs/Root/Zone')
    requester = mock_requester(response_spec=['json'], json=metadata)
    storage = mock_storage(spec=['get_zone_root', 'save_zone_root'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_YES
    expected = {
        'errors': ['url "/en-US/docs/Root/Zone" should be the non-zone path'],
        'doc_locale': 'en-US',
        'metadata_locale': 'en-US',
        'metadata_url': '/en-US/docs/Root/Zone',
        'zone_path': '/en-US/docs/Root/Zone',
    }
    storage.save_zone_root.assert_called_once_with(
        '/en-US/docs/Root/Zone', expected)


def test_extract_locale_mismatch_is_error():
    """
    If the metadata locale doesn't match the URL, it is an error.

    This appears to be common on zoned URLs with only one translation,
    and requires reseting the stored JSON data.
    """
    source = ZoneRootSource('/en-US/Zone')
    metadata = {
        'url': '/es/docs/Root/Zone',
        'locale': 'es'
    }
    data = source.extract_data(metadata)
    expected = {
        'errors': ['locale "es" should be the same as the path locale'],
        'doc_locale': 'en-US',
        'metadata_locale': 'es',
        'metadata_url': '/es/docs/Root/Zone',
        'zone_path': '/en-US/Zone',
    }
    assert data == expected
