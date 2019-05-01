"""
Test WikiDocumentType.

Integration tests against an ElasticSearch server are in kuma/search/tests/
"""
import mock
import pytest

from kuma.wiki.search import WikiDocumentType


@pytest.fixture
def mock_doc():
    """A mock Document that should update."""
    mock_doc = mock.Mock(
        spec_set=['is_redirect', 'deleted', 'slug'])
    mock_doc.is_redirect = False
    mock_doc.deleted = False
    mock_doc.slug = 'RegularSlug'
    return mock_doc


def test_should_update_standard_doc(mock_doc):
    """The mock_doc should update search index."""
    assert WikiDocumentType.should_update(mock_doc)


@pytest.mark.parametrize(
    'slug', ('Talk:Web' 'Web/Talk:CSS', 'User:jezdez',
             'User_talk:jezdez', 'Template_talk:anch',
             'Project_talk:MDN', 'Experiment:Blue'))
def test_should_not_update_excluded_slug(mock_doc, slug):
    """Excluded slugs should not update the search index."""
    mock_doc.slug = slug
    assert not WikiDocumentType.should_update(mock_doc)


@pytest.mark.parametrize('flag', 'is_redirect')
def test_should_not_update_excluded_flags(mock_doc, flag):
    """Do not update the search index if some flags are set."""
    setattr(mock_doc, flag, True)
    assert not WikiDocumentType.should_update(mock_doc)
