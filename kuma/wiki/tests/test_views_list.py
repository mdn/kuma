from __future__ import unicode_literals

import pytest
from django.conf import settings
from pyquery import PyQuery as pq

from kuma.core.tests import assert_shared_cache_header
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams

from ..models import Document


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
@pytest.mark.parametrize(
    'endpoint',
    ['tag', 'list_tags', 'all_documents', 'errors',
     'without_parent', 'top_level', 'list_review_tag', 'list_review',
     'list_with_localization_tag', 'list_with_localization_tags'])
def test_disallowed_methods(db, client, http_method, endpoint):
    """HTTP methods other than GET & HEAD are not allowed."""
    kwargs = None
    if endpoint in ('tag', 'list_review_tag', 'list_with_localization_tag'):
        kwargs = dict(tag='tag')
    url = reverse('wiki.{}'.format(endpoint), kwargs=kwargs)
    resp = getattr(client, http_method)(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 405
    assert_shared_cache_header(resp)


def test_revisions(root_doc, client):
    """$history of English doc works."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,))
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)


def test_revisions_of_translated_document(trans_doc, client):
    """
    $history for translated documents includes an English revision.

    This is the revision the first translation was based on.
    """
    assert trans_doc.revisions.count() == 1
    url = reverse('wiki.document_revisions', args=(trans_doc.slug,),
                  locale=trans_doc.locale)
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
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
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    page = pq(resp.content)
    list_content = page('.revision-list-contain').find('li')
    assert len(list_content) == 1  # The translation alone


def test_revisions_bad_slug_is_not_found(db, client):
    """$history of unknown page returns 404."""
    url = reverse('wiki.document_revisions', args=('not_found',))
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 404


def test_revisions_doc_without_revisions_is_not_found(db, client):
    """$history of half-created document returns 404."""
    doc = Document.objects.create(locale='en-US', slug='half_created')
    url = reverse('wiki.document_revisions', args=(doc.slug,))
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 404


def test_revisions_all_params_as_anon_user_is_forbidden(root_doc, client):
    """Anonymous users are forbidden to request all revisions."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,))
    all_url = urlparams(url, limit='all')
    resp = client.get(all_url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 403
    assert_shared_cache_header(resp)


def test_revisions_all_params_as_user_is_allowed(root_doc, wiki_user, client):
    """Users are allowed to request all revisions."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,))
    all_url = urlparams(url, limit='all')
    wiki_user.set_password('password')
    wiki_user.save()
    client.login(username=wiki_user.username, password='password')
    resp = client.get(all_url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200


def test_revisions_request_tiny_pages(edit_revision, client):
    """$history will paginate the revisions."""
    doc = edit_revision.document
    assert doc.revisions.count() > 1
    url = reverse('wiki.document_revisions', args=(doc.slug,))
    limit_url = urlparams(url, limit=1)
    resp = client.get(limit_url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    page = pq(resp.content)
    assert len(page.find('ol.pagination')) == 1


def test_revisions_request_large_pages(root_doc, client):
    """$history?limit=(more than revisions) works, removes pagination."""
    rev_count = root_doc.revisions.count()
    url = reverse('wiki.document_revisions', args=(root_doc.slug,))
    limit_url = urlparams(url, limit=rev_count + 1)
    resp = client.get(limit_url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    page = pq(resp.content)
    assert len(page.find('ol.pagination')) == 0


def test_revisions_request_invalid_pages(root_doc, client):
    """$history?limit=nonsense uses the default pagination."""
    url = reverse('wiki.document_revisions', args=(root_doc.slug,))
    limit_url = urlparams(url, limit='nonsense')
    resp = client.get(limit_url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200


def test_list_no_redirects(redirect_doc, doc_hierarchy, client):
    url = reverse('wiki.all_documents')
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert 'text/html' in resp['Content-Type']
    # There should be 4 documents in the 'en-US' locale from
    # doc_hierarchy, plus the root_doc (which is pulled-in by
    # the redirect_doc), but the redirect_doc should not be one of them.
    assert len(pq(resp.content).find('.document-list li')) == 5
    assert redirect_doc.slug.encode('utf-8') not in resp.content


def test_tags(root_doc, client):
    """Test list of all tags."""
    root_doc.tags.set('foobar', 'blast')
    url = reverse('wiki.list_tags')
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    assert b'foobar' in resp.content
    assert b'blast' in resp.content
    assert 'wiki/list/tags.html' in [t.name for t in resp.templates]
    assert_shared_cache_header(resp)


@pytest.mark.tags
@pytest.mark.parametrize('tag', ['foo', 'bar'])
@pytest.mark.parametrize('tag_case', ['lower', 'upper'])
@pytest.mark.parametrize('locale_case', ['root', 'trans'])
def test_tag_list(root_doc, trans_doc, client, locale_case, tag_case, tag):
    """
    Verify the tagged documents list view. Tags should be case
    insensitive (https://bugzil.la/976071).
    """
    tag_query = getattr(tag, tag_case)()
    root_doc.tags.set('foo', 'bar')
    trans_doc.tags.set('foo', 'bar')
    exp_doc = root_doc if (locale_case == 'root') else trans_doc
    url = reverse('wiki.tag', locale=exp_doc.locale, kwargs={'tag': tag_query})
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    dom = pq(resp.content)
    selector = 'ul.document-list li a[href="/{}/docs/{}"]'
    assert len(dom('#document-list ul.document-list li')) == 1
    assert len(dom.find(selector.format(exp_doc.locale, exp_doc.slug))) == 1

    # Changing the tags to something other than what we're
    # searching for should take the results to zero.
    root_doc.tags.set('foobar')
    trans_doc.tags.set('foobar')

    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    dom = pq(resp.content)
    assert len(dom('#document-list ul.document-list li')) == 0
    assert root_doc.slug not in resp.content.decode('utf-8')
    assert trans_doc.slug not in resp.content.decode('utf-8')


@pytest.mark.parametrize('locale', ['en-US', 'de', 'fr'])
def test_list_with_errors(redirect_doc, doc_hierarchy, client, locale):
    top_doc = doc_hierarchy.top
    bottom_doc = doc_hierarchy.bottom
    de_doc = top_doc.translated_to('de')
    for doc in (top_doc, bottom_doc, de_doc, redirect_doc):
        doc.rendered_errors = 'bad render'
        doc.save()

    if locale == 'en-US':
        exp_docs = (top_doc, bottom_doc)
    elif locale == 'de':
        exp_docs = (de_doc,)
    else:  # fr
        exp_docs = ()

    url = reverse('wiki.errors', locale=locale)
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    dom = pq(resp.content)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert 'text/html' in resp['Content-Type']
    assert len(dom.find('.document-list li')) == len(exp_docs)
    selector = 'ul.document-list li a[href="/{}/docs/{}"]'
    for doc in exp_docs:
        assert len(dom.find(selector.format(doc.locale, doc.slug))) == 1


@pytest.mark.parametrize('locale', ['en-US', 'de', 'fr'])
def test_list_without_parent(redirect_doc, root_doc, doc_hierarchy, client,
                             locale):
    if locale == 'en-US':
        exp_docs = (root_doc,
                    doc_hierarchy.top,
                    doc_hierarchy.middle_top,
                    doc_hierarchy.middle_bottom,
                    doc_hierarchy.bottom)
    else:  # All translations have a parent.
        exp_docs = ()

    url = reverse('wiki.without_parent', locale=locale)
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    dom = pq(resp.content)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert 'text/html' in resp['Content-Type']
    assert len(dom.find('.document-list li')) == len(exp_docs)
    selector = 'ul.document-list li a[href="/{}/docs/{}"]'
    for doc in exp_docs:
        assert len(dom.find(selector.format(doc.locale, doc.slug))) == 1


@pytest.mark.parametrize('locale', ['en-US', 'de', 'fr'])
def test_list_top_level(redirect_doc, root_doc, doc_hierarchy, client, locale):
    if locale == 'en-US':
        exp_docs = (root_doc, doc_hierarchy.top)
    else:
        exp_docs = (doc_hierarchy.top.translated_to(locale),)

    url = reverse('wiki.top_level', locale=locale)
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    dom = pq(resp.content)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert 'text/html' in resp['Content-Type']
    assert len(dom.find('.document-list li')) == len(exp_docs)
    selector = 'ul.document-list li a[href="/{}/docs/{}"]'
    for doc in exp_docs:
        assert len(dom.find(selector.format(doc.locale, doc.slug))) == 1


@pytest.mark.parametrize('locale', ['en-US', 'de', 'fr'])
def test_list_with_localization_tag(redirect_doc, doc_hierarchy, client,
                                    locale):
    top_doc = doc_hierarchy.top
    bottom_doc = doc_hierarchy.bottom
    de_doc = top_doc.translated_to('de')
    for doc in (top_doc, bottom_doc, de_doc, redirect_doc):
        doc.current_revision.localization_tags.set('inprogress')

    if locale == 'en-US':
        exp_docs = (top_doc, bottom_doc)
    elif locale == 'de':
        exp_docs = (de_doc,)
    else:  # fr
        exp_docs = ()

    url = reverse('wiki.list_with_localization_tag', locale=locale,
                  kwargs={'tag': 'inprogress'})
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    dom = pq(resp.content)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert 'text/html' in resp['Content-Type']
    assert len(dom.find('.document-list li')) == len(exp_docs)
    selector = 'ul.document-list li a[href="/{}/docs/{}"]'
    for doc in exp_docs:
        assert len(dom.find(selector.format(doc.locale, doc.slug))) == 1


@pytest.mark.parametrize('locale', ['en-US', 'de', 'fr'])
def test_list_with_localization_tags(redirect_doc, doc_hierarchy, client,
                                     locale):
    top_doc = doc_hierarchy.top
    bottom_doc = doc_hierarchy.bottom
    de_doc = top_doc.translated_to('de')
    for doc in (top_doc, bottom_doc, de_doc, redirect_doc):
        doc.current_revision.localization_tags.set('inprogress')

    if locale == 'en-US':
        exp_docs = (top_doc, bottom_doc)
    elif locale == 'de':
        exp_docs = (de_doc,)
    else:  # fr
        exp_docs = ()

    url = reverse('wiki.list_with_localization_tags', locale=locale)
    resp = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    dom = pq(resp.content)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert 'text/html' in resp['Content-Type']
    assert len(dom.find('.document-list li')) == len(exp_docs)
    selector = 'ul.document-list li a[href="/{}/docs/{}"]'
    for doc in exp_docs:
        assert len(dom.find(selector.format(doc.locale, doc.slug))) == 1
