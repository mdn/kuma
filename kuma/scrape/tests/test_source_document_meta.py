"""Tests for the DocumentMetaSource class ($json API)."""


from . import mock_requester, mock_storage
from ..sources import DocumentMetaSource


# Partial meta from
# /en-US/docs/Learn/Getting_started_with_the_web$json
meta_with_trans = {
    'id': 125461,
    'locale': 'en-US',
    'slug': 'Learn/Getting_started_with_the_web',
    'translations': [
        {
            'locale': 'fr',
            'url': '/fr/docs/Apprendre/Commencer_avec_le_web',
        }, {
            'locale': 'tr',
            'url': '/tr/docs/%C3%96%C4%9Fren/Getting_started_with_the_web',
        }],
    'url': '/en-US/docs/Learn/Getting_started_with_the_web'
}

meta_without_trans = {
    'id': 101,
    'translations': [],
    'url': '/en-US/docs/Parent/Child',
}


def test_gather_no_resources():
    """All metadata prereqs can be satisfied in the first call."""
    opts = {
        'translations': True,
        'depth': 5,
    }
    source = DocumentMetaSource(meta_without_trans['url'], **opts)
    requester = mock_requester(
        response_spec=['status_code', 'json'], status_code=200,
        json=meta_without_trans)
    storage = mock_storage(
        spec=['get_document_metadata', 'save_document_metadata'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    storage.save_document_metadata.assert_called_once_with(
        'en-US', 'Parent/Child', meta_without_trans)


def test_gather_uses_stored():
    """All metadata prereqs can be satisfied in the first call."""
    source = DocumentMetaSource('/en-US/docs/Done')
    requester = mock_requester()
    storage = mock_storage(spec=['get_document_metadata'])
    storage.get_document_metadata.return_value = meta_without_trans
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_NO


def test_gather_error():
    """If the metadata 404s, the source is in error."""
    source = DocumentMetaSource('/en-US/docs/Error')
    requester = mock_requester(response_spec=['status_code'], status_code=404)
    storage = mock_storage(
        spec=['get_document_metadata', 'save_document_metadata'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_YES
    storage.save_document_metadata.assert_called_once_with(
        'en-US', 'Error', {'error': 'status code 404'})


def test_extract_translations():
    """If translations are requested, they are extracted from metadata."""
    opts = {'translations': True}
    source = DocumentMetaSource(meta_with_trans['url'], **opts)
    result = source.extract_data(meta_with_trans)
    assert result == [
        ('document', '/fr/docs/Apprendre/Commencer_avec_le_web', {}),
        ('document',
            '/tr/docs/Öğren/Getting_started_with_the_web', {}),
    ]


def test_extract_translation_with_depth():
    """Child resources also get the translations request."""
    opts = {'translations': True, 'depth': 1}
    source = DocumentMetaSource(meta_with_trans['url'], **opts)
    result = source.extract_data(meta_with_trans)
    result_opts = {'depth': 1}
    assert result == [
        ('document', '/fr/docs/Apprendre/Commencer_avec_le_web',
            result_opts),
        ('document',
            '/tr/docs/Öğren/Getting_started_with_the_web',
            result_opts),
    ]


def test_extract_translation_with_revisions():
    """Child resources also get the revisions request."""
    opts = {'translations': True, 'revisions': 5}
    source = DocumentMetaSource(meta_with_trans['url'], **opts)
    result = source.extract_data(meta_with_trans)
    result_opts = {'revisions': 5}
    assert result == [
        ('document', '/fr/docs/Apprendre/Commencer_avec_le_web',
            result_opts),
        ('document', '/tr/docs/Öğren/Getting_started_with_the_web',
            result_opts),
    ]
