import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from pyquery import PyQuery as pq

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse

from ..models import Document, Revision


# dict of case-name --> tuple of slug and expected status code
SLUG_SIMPLE_CASES = {
    'invalid_slash': 'Foo/bar',
    'invalid_dollar_sign': 'Foo$bar',
    'invalid_question_mark': 'Foo?bar',
    'invalid_percent_sign': 'Foo%bar',
    'invalid_double_quote': 'Foo"bar',
    'invalid_single_quote': "Foo'bar",
    'invalid_whitespace': 'Foo bar',
}
SLUG_RESERVED_CASES = {
    'invalid_reserved_01': 'ckeditor_config.js',
    'invalid_reserved_02': 'preview-wiki-content',
    'invalid_reserved_03': 'get-documents',
    'invalid_reserved_04': 'tags',
    'invalid_reserved_05': 'tag/editorial',
    'invalid_reserved_06': 'new',
    'invalid_reserved_07': 'all',
    'invalid_reserved_08': 'with-errors',
    'invalid_reserved_09': 'without-parent',
    'invalid_reserved_10': 'top-level',
    'invalid_reserved_11': 'needs-review',
    'invalid_reserved_12': 'needs-review/technical',
    'invalid_reserved_13': 'localization-tag',
    'invalid_reserved_14': 'localization-tag/inprogress',
    'invalid_reserved_15': 'templates',
    'invalid_reserved_16': 'submit_akismet_spam',
    'invalid_reserved_17': 'feeds/atom/all',
    'invalid_reserved_18': 'feeds/rss/all',
    'invalid_reserved_19': 'feeds/atom/l10n-updates',
    'invalid_reserved_20': 'feeds/rss/l10n-updates',
    'invalid_reserved_21': 'feeds/atom/tag/editorial',
    'invalid_reserved_22': 'feeds/atom/needs-review',
    'invalid_reserved_23': 'feeds/rss/needs-review',
    'invalid_reserved_24': 'feeds/atom/needs-review/technical',
    'invalid_reserved_25': 'feeds/atom/revisions',
    'invalid_reserved_26': 'feeds/rss/revisions',
    'invalid_reserved_27': 'feeds/atom/files',
    'invalid_reserved_28': 'feeds/rss/files',
}


@pytest.fixture
def permission_add_document(db):
    return Permission.objects.get(codename='add_document')


@pytest.fixture
def add_doc_client(editor_client, wiki_user, permission_add_document):
    wiki_user.user_permissions.add(permission_add_document)
    return editor_client


def test_check_read_only_mode(user_client):
    response = user_client.get(reverse('wiki.create'),
                               HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 403
    assert_no_cache_header(response)


def test_user_add_document_permission(editor_client):
    response = editor_client.get(reverse('wiki.create'),
                                 HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 403
    assert response['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(response)


@pytest.mark.toc
def test_get(add_doc_client):
    response = add_doc_client.get(reverse('wiki.create'),
                                  HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(response)
    page = pq(response.content)
    toc_select = page.find('#id_toc_depth')
    toc_options = toc_select.find('option')
    found_selected = False
    for option in toc_options:
        opt_element = pq(option)
        if opt_element.attr('selected'):
            found_selected = True
            assert opt_element.attr('value') == str(Revision.TOC_DEPTH_H4)
    assert found_selected, 'No ToC depth initially selected.'
    # Check discard button.
    assert (page.find('.btn-discard').attr('href') == reverse('wiki.create'))


@pytest.mark.tags
@pytest.mark.review_tags
def test_create_valid(add_doc_client):
    """Test creating a new document with valid and invalid slugs."""
    slug = 'Foobar'
    data = dict(
        title='A Foobar Document',
        slug=slug,
        tags='tag1, tag2',
        review_tags=['editorial', 'technical'],
        keywords='key1, key2',
        summary='lipsum',
        content='lorem ipsum dolor sit amet',
        comment='This is foobar.',
        toc_depth=1,
    )
    url = reverse('wiki.create')
    resp = add_doc_client.post(url, data, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 302
    assert resp['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(resp)
    assert resp['Location'].endswith(reverse('wiki.document', args=(slug,)))
    doc = Document.objects.get(slug=slug)
    for name in (set(data.keys()) - set(('tags', 'review_tags'))):
        assert getattr(doc.current_revision, name) == data[name]
    assert (sorted(doc.tags.all().values_list('name', flat=True)) ==
            ['tag1', 'tag2'])
    review_tags = doc.current_revision.review_tags
    assert (sorted(review_tags.all().values_list('name', flat=True)) ==
            ['editorial', 'technical'])


@pytest.mark.tags
@pytest.mark.review_tags
@pytest.mark.parametrize(
    'slug',
    list(SLUG_SIMPLE_CASES.values()) + list(SLUG_RESERVED_CASES.values()),
    ids=list(SLUG_SIMPLE_CASES) + list(SLUG_RESERVED_CASES))
def test_create_invalid(add_doc_client, slug):
    """Test creating a new document with valid and invalid slugs."""
    data = dict(
        title='A Foobar Document',
        slug=slug,
        tags='tag1, tag2',
        review_tags=['editorial', 'technical'],
        keywords='key1, key2',
        summary='lipsum',
        content='lorem ipsum dolor sit amet',
        comment='This is foobar.',
        toc_depth=1,
    )
    url = reverse('wiki.create')
    resp = add_doc_client.post(url, data, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    assert resp['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(resp)
    assert b'The slug provided is not valid.' in resp.content
    with pytest.raises(Document.DoesNotExist):
        Document.objects.get(slug=slug, locale='en-US')
    assert pq(resp.content).find('input[name=slug]')[0].value == slug


@pytest.mark.tags
@pytest.mark.review_tags
@pytest.mark.parametrize('slug', ['Foobar', 'Root'])
def test_create_child_valid(root_doc, add_doc_client, slug):
    """Test creating a new child document with valid and invalid slugs."""
    data = dict(
        title='A Child of the Root Document',
        slug=slug,
        tags='tag1, tag2',
        review_tags=['editorial', 'technical'],
        keywords='key1, key2',
        summary='lipsum',
        content='lorem ipsum dolor sit amet',
        comment='This is foobar.',
        toc_depth=1,
    )
    url = reverse('wiki.create')
    url += '?parent={}'.format(root_doc.id)
    full_slug = '{}/{}'.format(root_doc.slug, slug)
    resp = add_doc_client.post(url, data, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 302
    assert resp['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(resp)
    assert resp['Location'].endswith(
        reverse('wiki.document', args=(full_slug,)))
    assert root_doc.children.count() == 1
    doc = Document.objects.get(slug=full_slug, locale='en-US')
    skip_keys = set(('tags', 'review_tags', 'parent_topic'))
    for name in (set(data.keys()) - skip_keys):
        expected = full_slug if name == 'slug' else data[name]
        assert getattr(doc.current_revision, name) == expected
    assert (sorted(doc.tags.all().values_list('name', flat=True)) ==
            ['tag1', 'tag2'])
    review_tags = doc.current_revision.review_tags
    assert (sorted(review_tags.all().values_list('name', flat=True)) ==
            ['editorial', 'technical'])


@pytest.mark.tags
@pytest.mark.review_tags
@pytest.mark.parametrize(
    'slug',
    list(SLUG_SIMPLE_CASES.values()),
    ids=list(SLUG_SIMPLE_CASES))
def test_create_child_invalid(root_doc, add_doc_client, slug):
    """Test creating a new child document with valid and invalid slugs."""
    data = dict(
        title='A Child of the Root Document',
        slug=slug,
        tags='tag1, tag2',
        review_tags=['editorial', 'technical'],
        keywords='key1, key2',
        summary='lipsum',
        content='lorem ipsum dolor sit amet',
        comment='This is foobar.',
        toc_depth=1,
    )
    url = reverse('wiki.create')
    url += '?parent={}'.format(root_doc.id)
    full_slug = '{}/{}'.format(root_doc.slug, slug)
    resp = add_doc_client.post(url, data, HTTP_HOST=settings.WIKI_HOST)
    assert resp.status_code == 200
    assert resp['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(resp)
    assert b'The slug provided is not valid.' in resp.content
    with pytest.raises(Document.DoesNotExist):
        Document.objects.get(slug=full_slug, locale='en-US')
    page = pq(resp.content)
    assert page.find('input[name=slug]')[0].value == slug


def test_clone_get(root_doc, add_doc_client):
    url = reverse('wiki.create')
    url += '?clone={}'.format(root_doc.id)
    response = add_doc_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(response)
    page = pq(response.content)
    assert page.find('input[name=slug]')[0].value is None
    assert page.find('input[name=title]')[0].value is None
    assert (page.find('textarea[name=content]')[0].value.strip() ==
            root_doc.current_revision.content)
