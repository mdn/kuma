"""Tests for the DocumentBaseSource class."""


import pytest

from kuma.scrape.sources import DocumentBaseSource


def test_top_level_doc():
    """A DocumentBaseSource with a top-level slug has no parent."""
    source = DocumentBaseSource('/locale/docs/slug')
    assert source.path == '/locale/docs/slug'
    assert source.locale == 'locale'
    assert source.slug == 'slug'
    assert source.parent_slug is None
    assert source.parent_path is None


def test_child_doc():
    """A DocumentBaseSource with a child-level slug has a parent."""
    source = DocumentBaseSource('/locale/docs/parent/child')
    assert source.path == '/locale/docs/parent/child'
    assert source.locale == 'locale'
    assert source.slug == 'parent/child'
    assert source.parent_slug == 'parent'
    assert source.parent_path == '/locale/docs/parent'


def test_url_escaped_raises():
    """Initializing with a URL-encoded path raises an exception."""
    with pytest.raises(ValueError):
        DocumentBaseSource('/en-US/docs/traducci%C3%B3n')
