# -*- coding: utf-8 -*-
"""Tests for kuma.wiki.views.revision."""
import pytest
from django.conf import settings

from kuma.core.tests import assert_shared_cache_header
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams

from ..models import Document, Revision


@pytest.mark.parametrize('raw', [True, False])
def test_compare_revisions(edit_revision, client, raw):
    """Comparing two valid revisions of the same document works."""
    doc = edit_revision.document
    first_revision = doc.revisions.first()
    params = {'from': first_revision.id, 'to': edit_revision.id}
    if raw:
        params['raw'] = '1'
    url = urlparams(reverse('wiki.compare_revisions', args=[doc.slug]),
                    **params)

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert_shared_cache_header(response)


@pytest.mark.parametrize('raw', [True, False])
def test_compare_translation(trans_revision, client, raw):
    """A localized revision can be compared to an English source revision."""
    fr_doc = trans_revision.document
    en_revision = trans_revision.based_on
    en_doc = en_revision.document
    assert en_doc != fr_doc
    params = {'from': en_revision.id, 'to': trans_revision.id}
    if raw:
        params['raw'] = '1'
    url = urlparams(reverse('wiki.compare_revisions', args=[fr_doc.slug],
                            locale=fr_doc.locale), **params)

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert_shared_cache_header(response)


@pytest.mark.parametrize('raw', [True, False])
def test_compare_revisions_without_tidied_content(edit_revision, client, raw):
    """Comparing revisions without tidied content displays a wait message."""
    doc = edit_revision.document
    first_revision = doc.revisions.first()

    # update() to skip the tidy_revision_content post_save signal handler
    ids = [first_revision.id, edit_revision.id]
    Revision.objects.filter(id__in=ids).update(tidied_content='')

    params = {'from': first_revision.id, 'to': edit_revision.id}
    if raw:
        params['raw'] = '1'
    url = urlparams(reverse('wiki.compare_revisions', args=[doc.slug]),
                    **params)

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert b'Please refresh this page in a few minutes.' in response.content


@pytest.mark.parametrize("id1,id2",
                         [('1e309', '1e309'),
                          ('', 'invalid'),
                          ('invalid', ''),
                          ])
def test_compare_revisions_invalid_ids(root_doc, client, id1, id2):
    """Comparing badly-formed revision parameters return 404, not error."""
    url = urlparams(reverse('wiki.compare_revisions', args=[root_doc.slug]),
                    **{'from': id1, 'to': id2})
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404


@pytest.mark.parametrize('param', ['from', 'to'])
def test_compare_revisions_only_one_param(create_revision, client, param):
    """If a compare query parameter is missing, a 404 is returned."""
    doc = create_revision.document
    url = urlparams(reverse('wiki.compare_revisions', args=[doc.slug]),
                    **{param: create_revision.id})
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404


def test_compare_revisions_wrong_document(edit_revision, client):
    """If the revision is for the wrong document, a 404 is returned."""
    doc = edit_revision.document
    first_revision = doc.revisions.first()
    other_doc = Document.objects.create(locale='en-US', slug='Other',
                                        title='Other Document')
    url = urlparams(reverse('wiki.compare_revisions', args=[other_doc.slug]),
                    **{'from': first_revision.id, 'to': edit_revision.id})
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404
