from datetime import datetime

import pytest

from ..constants import REDIRECT_CONTENT
from ..models import (Document, DocumentTag, LocalizationTag, ReviewTag,
                      Revision)


@pytest.fixture
def redirect_doc(root_doc, wiki_user):
    """A redirect document."""
    html = REDIRECT_CONTENT % {'href': root_doc.get_absolute_url(),
                               'title': root_doc.title}
    doc = Document.objects.create(locale='en-US', slug='OldRoot', html=html)
    doc.current_revision = Revision.objects.create(
        document=doc,
        creator=wiki_user,
        content=html,
        created=datetime(2017, 10, 27, 17, 4))
    doc.save()
    return doc


@pytest.fixture
def archive_doc(wiki_user):
    """An archived document."""
    archive = Document.objects.create(locale='en-US', slug='Archive',
                                      title='Archive of obsolete content')
    doc = Document.objects.create(locale='en-US', slug='Archive/Doc',
                                  title='Archived document',
                                  parent_topic=archive)
    doc.current_revision = Revision.objects.create(
        document=doc,
        creator=wiki_user,
        content='<p>Obsolete content.</p>',
        comment='Obsolete content',
        created=datetime(2017, 10, 27, 15, 48))
    doc.save()
    return doc


def test_get_natural_key(root_doc):
    """The locale + slug is the natural key for Documents."""
    assert root_doc.natural_key() == (root_doc.locale, root_doc.slug)
    assert root_doc == Document.objects.get_by_natural_key(root_doc.locale,
                                                           root_doc.slug)


@pytest.mark.parametrize(
    'legacy_slug',
    ('User:ethertank',
     'Talk:Developer_Guide/Build_Instructions/Windows_Prerequisites',
     'User_talk:ethertank',
     'Template_talk:anch',
     'Project_talk:To-do_list',
     ))
def test_documents_filter_for_list_exclude_slug_prefixes(root_doc, legacy_slug):
    """filter_for_list excludes some slug prefixes."""
    Document.objects.create(locale='en-US', slug=legacy_slug)
    results = Document.objects.filter_for_list()
    assert len(results) == 1
    assert results[0] == root_doc


def test_documents_filter_for_list_exclude_redirects(root_doc, redirect_doc):
    """filter_for_list excludes redirects"""
    assert list(Document.objects.filter_for_list()) == [root_doc]


def test_documents_filter_for_list_by_locale(root_doc, trans_doc):
    """filter_for_list can filter by locale."""
    results = Document.objects.filter_for_list(locale=trans_doc.locale)
    assert list(results) == [trans_doc]


def test_documents_filter_for_list_by_tag(root_doc):
    """filter_for_list can filter by a DocumentTag."""
    tag_foo = DocumentTag.objects.create(name='foo')
    tag_bar = DocumentTag.objects.create(name='bar')
    root_doc.tags.add(tag_foo)
    assert list(Document.objects.filter_for_list(tag=tag_foo)) == [root_doc]
    assert len(Document.objects.filter_for_list(tag=tag_bar)) == 0


def test_documents_filter_for_list_by_tag_name(root_doc):
    """filter_for_list can filter by a DocumentTag name."""
    tag_foo = DocumentTag.objects.create(name='foo')
    root_doc.tags.add(tag_foo)
    assert list(Document.objects.filter_for_list(tag_name='foo')) == [root_doc]
    assert len(Document.objects.filter_for_list(tag_name='bar')) == 0


def test_documents_filter_for_list_by_errors(root_doc):
    """filter_for_list can filter by Documents with render errors."""
    assert root_doc.rendered_errors is None
    assert len(Document.objects.filter_for_list(errors=True)) == 0
    root_doc.rendered_errors = '[]'
    root_doc.save()
    assert len(Document.objects.filter_for_list(errors=True)) == 0
    root_doc.rendered_errors = '[{"name": "kumascript", "level": "error"}]'
    root_doc.save()
    assert list(Document.objects.filter_for_list(errors=True)) == [root_doc]


def test_documents_filter_for_list_by_noparent(root_doc, trans_doc):
    """filter_for_list can filter by Documents with no parent."""
    assert list(Document.objects.filter_for_list(noparent=True)) == [root_doc]
    result = Document.objects.filter_for_list(locale=trans_doc.locale,
                                              noparent=True)
    assert len(result) == 0
    trans_doc.parent = None
    trans_doc.save()
    result = Document.objects.filter_for_list(locale=trans_doc.locale,
                                              noparent=True)
    assert list(result) == [trans_doc]


def test_documents_filter_for_list_by_toplevel(root_doc):
    """filter_for_list can filter by top-level Documents (no parent topic)."""
    Document.objects.create(locale=root_doc.locale,
                            parent_topic=root_doc,
                            slug=root_doc.slug + '/Child',
                            title='Child Document')
    assert len(Document.objects.filter_for_list()) == 2
    assert list(Document.objects.filter_for_list(toplevel=True)) == [root_doc]


def test_documents_filter_for_review(create_revision):
    """filter_for_review can filter all documents with a review tag."""
    assert len(Document.objects.filter_for_review()) == 0

    create_revision.review_tags.set('tag')
    doc = create_revision.document
    assert list(Document.objects.filter_for_review()) == [doc]


def test_documents_filter_for_review_by_locale(create_revision, trans_revision):
    """filter_for_review can filter by locale."""
    create_revision.review_tags.set('tag')
    trans_revision.review_tags.set('other_tag')
    assert len(Document.objects.filter_for_review()) == 2

    doc = create_revision.document
    resp = list(Document.objects.filter_for_review(locale=doc.locale))
    assert resp == [doc]


def test_documents_filter_for_review_by_tag_name(create_revision):
    """filter_for_review can filter by ReviewTtag name."""
    assert len(Document.objects.filter_for_review(tag_name='editorial')) == 0
    assert len(Document.objects.filter_for_review(tag_name='technical')) == 0

    create_revision.review_tags.set('editorial')
    resp = list(Document.objects.filter_for_review(tag_name='editorial'))
    assert resp == [create_revision.document]
    assert len(Document.objects.filter_for_review(tag_name='technical')) == 0


def test_documents_filter_for_review_by_tag(create_revision):
    """filter_for_review can filter by ReviewTag instance."""
    editorial, _ = ReviewTag.objects.get_or_create(name='editorial')
    technical, _ = ReviewTag.objects.get_or_create(name='technical')
    assert len(Document.objects.filter_for_review(tag=editorial)) == 0
    assert len(Document.objects.filter_for_review(tag=technical)) == 0

    create_revision.review_tags.add(technical)
    assert len(Document.objects.filter_for_review(tag=editorial)) == 0
    resp = list(Document.objects.filter_for_review(tag=technical))
    assert resp == [create_revision.document]


def test_documents_filter_for_review_excludes_redirects(redirect_doc):
    """bug 1274874: filter_for_review excludes redirects."""
    redirect_doc.current_revision.review_tags.set('editorial')
    resp = Document.objects.filter_for_review(tag_name='editorial')
    assert len(resp) == 0


def test_documents_filter_for_review_excludes_archive(archive_doc):
    """bug 1274874: filter_for_review excludes archive documents."""
    archive_doc.current_revision.review_tags.set('editorial')
    resp = Document.objects.filter_for_review(tag_name='editorial')
    assert len(resp) == 0


def test_documents_filter_with_localization_tag(create_revision):
    """filter_with_localization_tag can filter all documents."""
    assert len(Document.objects.filter_with_localization_tag()) == 0

    create_revision.localization_tags.set('tag')
    doc = create_revision.document
    assert list(Document.objects.filter_with_localization_tag()) == [doc]


def test_documents_filter_with_localization_tag_by_locale(create_revision,
                                                          trans_revision):
    """filter_with_localization_tag can filter by locale."""
    create_revision.localization_tags.set('tag')
    trans_revision.localization_tags.set('other_tag')
    assert len(Document.objects.filter_with_localization_tag()) == 2

    doc = create_revision.document
    resp = Document.objects.filter_with_localization_tag(locale=doc.locale)
    assert list(resp) == [doc]


def test_documents_filter_with_localization_tag_by_tag_name(create_revision):
    """filter_with_localization_tag can filter by LocalizationTag name."""
    tag = 'inprogress'
    resp = Document.objects.filter_with_localization_tag(tag_name=tag)
    assert len(resp) == 0

    create_revision.localization_tags.set('inprogress')
    resp = Document.objects.filter_with_localization_tag(tag_name=tag)
    assert list(resp) == [create_revision.document]


def test_documents_filter_with_localization_tag_by_tag(create_revision):
    """filter_with_localization_tag can filter by the instance."""
    inprogress = LocalizationTag.objects.create(name='inprogress')
    resp = Document.objects.filter_with_localization_tag(tag=inprogress)
    assert len(resp) == 0

    create_revision.localization_tags.add(inprogress)
    resp = Document.objects.filter_with_localization_tag(tag=inprogress)
    assert list(resp) == [create_revision.document]


def test_documents_filter_with_localization_tag_excludes_redirects(
        redirect_doc):
    """bug 1274874: filter_with_localization_tag excludes redirects."""
    tag = 'inprogress'
    redirect_doc.current_revision.localization_tags.set(tag)
    resp = Document.objects.filter_with_localization_tag(tag_name=tag)
    assert len(resp) == 0


def test_documents_filter_with_localization_tag_excludes_archive(archive_doc):
    """bug 1274874: filter_with_localization_tag excludes archive docs."""
    tag = 'inprogress'
    archive_doc.current_revision.localization_tags.set(tag)
    resp = Document.objects.filter_with_localization_tag(tag_name=tag)
    assert len(resp) == 0
