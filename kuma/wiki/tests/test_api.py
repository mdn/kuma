import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
def test_doc_api_disallowed_methods(client, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse('wiki.api.doc', args=['en-US', 'Web/CSS'])
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


def test_doc_api_404(client, root_doc):
    """We get a 404 if we ask for a document that does not exist."""
    url = reverse('wiki.api.doc', args=['en-US', 'NoSuchPage'])
    response = getattr(client, 'get')(url)
    assert response.status_code == 404
    assert_no_cache_header(response)


def test_doc_api(client, trans_doc):
    """On success we get document details in a JSON response."""
    url = reverse('wiki.api.doc', args=[trans_doc.locale, trans_doc.slug])
    response = getattr(client, 'get')(url)
    assert response.status_code == 200
    assert_no_cache_header(response)

    data = response.json()
    assert data['locale'] == trans_doc.locale
    assert data['slug'] == trans_doc.slug
    assert data['id'] == trans_doc.id
    assert data['title'] == trans_doc.title
    assert data['language'] == trans_doc.language
    assert data['absoluteURL'] == trans_doc.get_absolute_url()
    assert data['redirectURL'] == trans_doc.get_redirect_url()
    assert data['editURL'] == trans_doc.get_edit_url()
    assert data['bodyHTML'] == trans_doc.get_body_html()
    assert data['quickLinksHTML'] == trans_doc.get_quick_links_html()
    assert data['tocHTML'] == trans_doc.get_toc_html()
    assert data['translations'] == [{
        'locale': 'en-US',
        'title': 'Root Document',
        'url': '/en-US/docs/Root'
    }]
