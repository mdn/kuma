"""Tests for the DocumentRedirectSource class (HEAD document)."""


from . import mock_requester, mock_storage
from ..sources import DocumentRedirectSource


def test_root_doc(root_doc, client):
    """Test a page without redirects."""
    url = root_doc.get_absolute_url()
    source = DocumentRedirectSource(url)
    requester = mock_requester()
    storage = mock_storage(spec=['save_document_redirect'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    storage.save_document_redirect.assert_called_once_with(
        'en-US', 'Root', {})


def test_redirect_no_path_change(root_doc, client):
    """
    Test a page with a redirect that doesn't change the path.

    For example, a page might redirect from http:// to https://.
    """
    url = root_doc.get_absolute_url()
    source = DocumentRedirectSource(url)
    requester = mock_requester(
        response_spec=['content', 'history', 'status_code', 'url'],
        history=[(301, url)],
        final_path=url)
    storage = mock_storage(spec=['save_document_redirect'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    storage.save_document_redirect.assert_called_once_with(
        'en-US', 'Root', {})


def test_redirect(root_doc, client):
    """Test a page with a redirect."""
    final_path = root_doc.get_absolute_url()
    url = final_path.replace(root_doc.slug, 'Redirect')
    source = DocumentRedirectSource(url)
    requester = mock_requester(
        response_spec=['content', 'history', 'status_code', 'url'],
        history=[(301, url)],
        final_path=final_path)
    storage = mock_storage(spec=['save_document_redirect'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    storage.save_document_redirect.assert_called_once_with(
        'en-US', 'Redirect', {'redirect_to': final_path})


def test_missing_doc(client):
    """
    A missing document results in an error.

    One cause: translations are requested, and a recently deleted
    translation is in the metadata.
    """
    source = DocumentRedirectSource('/en-US/docs/missing')
    requester = mock_requester(status_code=404)
    storage = mock_storage()
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
