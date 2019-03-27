import mock
import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.wiki.api.v1 import views

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


@mock.patch('kuma.wiki.jobs.DocumentContributorsJob.fetch_on_miss', True)
def test_doc_api(client, trans_doc, cleared_cacheback_cache):
    """On success we get document details in a JSON response."""

    # The fetch_on_miss mock and the cleared_cacheback_cache fixture
    # are here to ensure that we don't get an old cached value for
    # the contributors property, and also that we don't use []
    # while a celery job is running.
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
        'language': 'English (US)',
        'localizedLanguage': u'Anglais am\u00e9ricain',
        'title': 'Root Document',
        'url': '/en-US/docs/Root'
    }]
    assert data['contributors'] == ['wiki_user']
    assert data['lastModified'] == '2017-04-14T12:20:00'
    assert data['lastModifiedBy'] == 'wiki_user'

    # Also ensure that we get exactly the same data by calling
    # the document_api_data() function directly
    data2 = views.document_api_data(trans_doc)
    assert data == data2
