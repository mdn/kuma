from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from ..models import Document


def test_revisions(root_doc, client):
    """$history of English doc works."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,),
                  locale=root_doc.locale)
    resp = client.get(url)
    assert resp.status_code == 200


def test_revisions_of_translated_document(trans_doc, client):
    """
    $history for translated documents includes an English revision.

    This is the revision the first translation was based on.
    """
    assert trans_doc.revisions.count() == 1
    url = reverse('wiki.document_revisions', args=(trans_doc.slug,),
                  locale=trans_doc.locale)
    resp = client.get(url)
    assert resp.status_code == 200
    page = pq(resp.content)
    list_content = page('.revision-list-contain').find('li')
    assert len(list_content) == 2  # The translation plus the English revision
    eng_rev_id = list_content.find('input[name=from]')[1].attrib['value']
    assert str(trans_doc.current_revision.based_on_id) == eng_rev_id


def test_revisions_of_translated_doc_with_no_based_on(trans_revision, client):
    """
    $history for trans docs excludes the English revision if no based_on

    This can happen for old translated docs, or ones manually associated with
    the parent.
    """
    assert trans_revision.based_on
    trans_revision.based_on = None
    trans_revision.save()
    trans_doc = trans_revision.document
    url = reverse('wiki.document_revisions', args=(trans_doc.slug,),
                  locale=trans_doc.locale)
    resp = client.get(url)
    assert resp.status_code == 200
    page = pq(resp.content)
    list_content = page('.revision-list-contain').find('li')
    assert len(list_content) == 1  # The translation alone


def test_revisions_bad_slug_is_not_found(db, client):
    """$history of unknown page returns 404."""
    url = reverse('wiki.document_revisions', args=('not_found',),
                  locale='en-US')
    resp = client.get(url)
    assert resp.status_code == 404


def test_revisions_doc_without_revisions_is_not_found(db, client):
    """$history of half-created document returns 404."""
    doc = Document.objects.create(locale='en-US', slug='half_created')
    url = reverse('wiki.document_revisions', args=(doc.slug,),
                  locale=doc.locale)
    resp = client.get(url)
    assert resp.status_code == 404


def test_revisions_all_params_as_anon_user_is_forbidden(root_doc, client):
    """Anonymous users are forbidden to request all revisions."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,),
                  locale=root_doc.locale)
    all_url = urlparams(url, limit='all')
    resp = client.get(all_url)
    assert resp.status_code == 403


def test_revisions_all_params_as_user_is_allowed(root_doc, wiki_user, client):
    """Users are allowed to request all revisions."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,),
                  locale=root_doc.locale)
    all_url = urlparams(url, limit='all')
    wiki_user.set_password('password')
    wiki_user.save()
    client.login(username=wiki_user.username, password='password')
    resp = client.get(all_url)
    assert resp.status_code == 200


def test_revisions_request_tiny_pages(edit_revision, client):
    """$history will paginate the revisions."""
    doc = edit_revision.document
    assert doc.revisions.count() > 1
    url = reverse('wiki.document_revisions', args=(doc.slug,),
                  locale=doc.locale)
    limit_url = urlparams(url, limit=1)
    resp = client.get(limit_url)
    assert resp.status_code == 200
    page = pq(resp.content)
    assert len(page.find('ol.pagination')) == 1


def test_revisions_request_large_pages(root_doc, client):
    """$history?limit=(more than revisions) works, removes pagination."""
    rev_count = root_doc.revisions.count()
    url = reverse('wiki.document_revisions', args=(root_doc.slug,),
                  locale=root_doc.locale)
    limit_url = urlparams(url, limit=rev_count + 1)
    resp = client.get(limit_url)
    assert resp.status_code == 200
    page = pq(resp.content)
    assert len(page.find('ol.pagination')) == 0


def test_revisions_request_invalid_pages(root_doc, client):
    """$history?limit=nonsense uses the default pagination."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,),
                  locale=root_doc.locale)
    limit_url = urlparams(url, limit='nonsense')
    resp = client.get(limit_url)
    assert resp.status_code == 200
