"""
Tests for kuma/wiki/views/document.py

Legacy tests are in test_views.py.
"""
import base64
import json
from collections import namedtuple
from datetime import datetime

import mock
import pytest
import requests_mock
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test.client import BOUNDARY, encode_multipart, MULTIPART_CONTENT
from django.utils.http import quote_etag
from django.utils.six.moves.urllib.parse import quote, urlparse
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kuma.authkeys.models import Key
from kuma.core.models import IPBan
from kuma.core.tests import (assert_no_cache_header, assert_redirect_to_wiki,
                             assert_shared_cache_header)
from kuma.core.urlresolvers import reverse

from . import HREFLANG_TEST_CASES
from ..constants import REDIRECT_CONTENT
from ..events import EditDocumentEvent, EditDocumentInTreeEvent
from ..models import Document, Revision
from ..views.document import _apply_content_experiment
from ..views.utils import calculate_etag


AuthKey = namedtuple('AuthKey', 'key header')

EMPTY_IFRAME = '<iframe></iframe>'
SECTION1 = '<h3 id="S1">S1</h3><p>This is a page. Deal with it.</p>'
SECTION2 = '<h3 id="S2">S2</h3><p>This is a page. Deal with it.</p>'
SECTION3 = '<h3 id="S3">S3</h3><p>This is a page. Deal with it.</p>'
SECTION4 = '<h3 id="S4">S4</h3><p>This is a page. Deal with it.</p>'
SECTIONS = SECTION1 + SECTION2 + SECTION3 + SECTION4
SECTION_CASE_TO_DETAILS = {
    'no-section': (None, SECTIONS),
    'section': ('S1', SECTION1),
    'another-section': ('S3', SECTION3),
    'non-existent-section': ('S99', '')
}


def get_content(content_case, data):
    if content_case == 'multipart':
        return MULTIPART_CONTENT, encode_multipart(BOUNDARY, data)

    if content_case == 'json':
        return 'application/json', json.dumps(data)

    if content_case == 'html-fragment':
        return 'text/html', data['content']

    assert content_case == 'html'
    return 'text/html', """
        <html>
            <head>
                <title>%(title)s</title>
            </head>
            <body>%(content)s</body>
        </html>
    """ % data


@pytest.fixture
def section_doc(root_doc, wiki_user):
    """
    The content in this document's current revision contains multiple HTML
    elements with an "id" attribute (or "sections"), and also has a length
    greater than or equal to 200, which meets the compression threshold of
    the GZipMiddleware, if used.
    """
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, creator=wiki_user, content=SECTIONS)
    root_doc.save()
    return root_doc


@pytest.fixture
def ce_settings(settings):
    settings.CONTENT_EXPERIMENTS = [{
        'id': 'experiment-test',
        'ga_name': 'experiment-test',
        'param': 'v',
        'pages': {
            'en-US:Original': {
                'control': 'Original',
                'test': 'Experiment:Test/Variant',
            }
        }
    }]
    return settings


@pytest.fixture
def authkey(wiki_user):
    key = Key(user=wiki_user, description='Test Key 1')
    secret = key.generate_secret()
    key.save()
    auth = '%s:%s' % (key.key, secret)
    # TODO: Once Python 2/3 is gone, replace encodestring by encodebytes
    header = 'Basic %s' % base64.b64encode(auth.encode('utf-8')).decode('utf-8')
    return AuthKey(key=key, header=header)


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
@pytest.mark.parametrize(
    'endpoint', ['children', 'toc', 'json', 'json_slug'])
def test_disallowed_methods(client, http_method, endpoint):
    """HTTP methods other than GET & HEAD are not allowed."""
    headers = {}
    kwargs = None
    if endpoint != 'json':
        kwargs = dict(document_path='Web/CSS')
    if endpoint == 'toc':
        headers.update(HTTP_HOST=settings.WIKI_HOST)
    url = reverse('wiki.{}'.format(endpoint), kwargs=kwargs)
    response = getattr(client, http_method)(url, **headers)
    assert response.status_code == 405
    assert_shared_cache_header(response)


@pytest.mark.parametrize('method', ('GET', 'HEAD'))
@pytest.mark.parametrize('if_none_match', (None, 'match', 'mismatch'))
@pytest.mark.parametrize(
    'section_case',
    ('no-section', 'section', 'another-section', 'non-existent-section')
)
def test_api_safe(client, section_doc, section_case, if_none_match, method):
    """
    Test GET & HEAD on wiki.document_api endpoint.
    """
    section_id, exp_content = SECTION_CASE_TO_DETAILS[section_case]

    url = section_doc.get_absolute_url() + '$api'

    if section_id:
        url += '?section={}'.format(section_id)

    headers = dict(HTTP_HOST=settings.WIKI_HOST)

    if method == 'GET':
        # Starting with Django 1.11, condition headers will be
        # considered only for GET requests. The one exception
        # is a PUT request to the wiki.document_api endpoint,
        # but that's not relevant here.
        if if_none_match == 'match':
            response = getattr(client, method.lower())(url, **headers)
            assert 'etag' in response
            headers['HTTP_IF_NONE_MATCH'] = response['etag']
        elif if_none_match == 'mismatch':
            headers['HTTP_IF_NONE_MATCH'] = 'ABC'

    response = getattr(client, method.lower())(url, **headers)

    if (if_none_match == 'match') and (method == 'GET'):
        exp_content = ''
        assert response.status_code == 304
    else:
        assert response.status_code == 200
        assert_shared_cache_header(response)
        assert 'last-modified' not in response
        if method == 'GET':
            assert quote_etag(calculate_etag(exp_content)) in response['etag']
        assert (response['x-kuma-revision'] ==
                str(section_doc.current_revision_id))

    if method == 'GET':
        assert response.content == exp_content.decode('utf-8')


@pytest.mark.parametrize('user_case', ('authenticated', 'anonymous'))
def test_api_put_forbidden_when_no_authkey(client, user_client, root_doc,
                                           user_case):
    """
    A PUT to the wiki.document_api endpoint should forbid access without
    an authkey, even for logged-in users.
    """
    url = root_doc.get_absolute_url() + '$api'
    response = (client if user_case == 'anonymous' else user_client).put(
        url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 403
    assert_no_cache_header(response)


def test_api_put_unsupported_content_type(client, authkey):
    """
    A PUT to the wiki.document_api endpoint with an unsupported content
    type should return a 400.
    """
    url = '/en-US/docs/foobar$api'
    response = client.put(
        url,
        data='stuff',
        content_type='nonsense',
        HTTP_AUTHORIZATION=authkey.header,
        HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 400
    assert_shared_cache_header(response)


def test_api_put_authkey_tracking(client, authkey):
    """
    Revisions modified by PUT API should track the auth key used
    """
    url = '/en-US/docs/foobar$api'
    data = dict(
        title="Foobar, The Document",
        content='<p>Hello, I am foobar.</p>',
    )
    content_type, encoded_data = get_content('json', data)
    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        HTTP_AUTHORIZATION=authkey.header,
        HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 201
    assert_shared_cache_header(response)
    last_log = authkey.key.history.order_by('-pk').all()[0]
    assert last_log.action == 'created'

    data['title'] = 'Foobar, The New Document'
    content_type, encoded_data = get_content('json', data)
    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        HTTP_AUTHORIZATION=authkey.header,
        HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 205
    assert_shared_cache_header(response)
    last_log = authkey.key.history.order_by('-pk').all()[0]
    assert last_log.action == 'updated'


@pytest.mark.parametrize('if_match', (None, 'match', 'mismatch'))
@pytest.mark.parametrize(
    'content_case',
    ('multipart', 'json', 'html-fragment', 'html')
)
@pytest.mark.parametrize(
    'section_case',
    ('no-section', 'section', 'another-section', 'non-existent-section')
)
def test_api_put_existing(settings, client, section_doc, authkey, section_case,
                          content_case, if_match):
    """
    A PUT to the wiki.document_api endpoint should allow the modification
    of an existing document's content.
    """
    orig_rev_id = section_doc.current_revision_id
    section_id, section_content = SECTION_CASE_TO_DETAILS[section_case]

    url = section_doc.get_absolute_url() + '$api'

    if section_id:
        url += '?section={}'.format(section_id)

    headers = dict(HTTP_AUTHORIZATION=authkey.header,
                   HTTP_HOST=settings.WIKI_HOST)

    if if_match == 'match':
        response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert 'etag' in response
        headers['HTTP_IF_MATCH'] = response['etag']
    elif if_match == 'mismatch':
        headers['HTTP_IF_MATCH'] = 'ABC'

    data = dict(
        comment="I like this document.",
        title="New Sectioned Root Document",
        summary="An edited sectioned root document.",
        content=EMPTY_IFRAME + '<p>This is an edit.</p>',
        tags="tagA,tagB,tagC",
        review_tags="editorial,technical",
    )

    content_type, encoded_data = get_content(content_case, data)

    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        **headers
    )

    if content_case == 'html-fragment':
        expected_title = section_doc.title
    else:
        expected_title = data['title']

    if section_content:
        expected_content = SECTIONS.replace(section_content, data['content'])
    else:
        expected_content = SECTIONS

    assert_shared_cache_header(response)

    if if_match == 'mismatch':
        assert response.status_code == 412
    else:
        assert response.status_code == 205
        # Confirm that the PUT worked.
        section_doc.refresh_from_db()
        assert section_doc.current_revision_id != orig_rev_id
        assert section_doc.title == expected_title
        assert section_doc.html == expected_content
        if content_case in ('multipart', 'json'):
            rev = section_doc.current_revision
            assert rev.summary == data['summary']
            assert rev.comment == data['comment']
            assert rev.tags == data['tags']
            assert (set(rev.review_tags.names()) ==
                    set(data['review_tags'].split(',')))


@pytest.mark.parametrize('slug_case', ('root', 'child', 'nonexistent-parent'))
@pytest.mark.parametrize(
    'content_case',
    ('multipart', 'json', 'html-fragment', 'html')
)
@pytest.mark.parametrize('section_case', ('no-section', 'section'))
def test_api_put_new(settings, client, root_doc, authkey, section_case,
                     content_case, slug_case):
    """
    A PUT to the wiki.document_api endpoint should allow the creation
    of a new document and its initial revision.
    """
    locale = settings.WIKI_DEFAULT_LANGUAGE
    section_id, _ = SECTION_CASE_TO_DETAILS[section_case]

    if slug_case == 'root':
        slug = 'foobar'
    elif slug_case == 'child':
        slug = 'Root/foobar'
    else:
        slug = 'nonexistent/foobar'

    url_path = '/{}/docs/{}'.format(locale, slug)
    url = url_path + '$api'

    # The section_id should have no effect on the results, but we'll see.
    if section_id:
        url += '?section={}'.format(section_id)

    data = dict(
        comment="I like this document.",
        title="Foobar, The Document",
        summary="A sectioned document named foobar.",
        content=EMPTY_IFRAME + SECTIONS,
        tags="tagA,tagB,tagC",
        review_tags="editorial,technical",
    )

    content_type, encoded_data = get_content(content_case, data)

    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        HTTP_AUTHORIZATION=authkey.header,
        HTTP_HOST=settings.WIKI_HOST
    )

    if content_case == 'html-fragment':
        expected_title = slug
    else:
        expected_title = data['title']

    if slug_case == 'nonexistent-parent':
        assert response.status_code == 404
        assert_no_cache_header(response)
    else:
        assert response.status_code == 201
        assert_shared_cache_header(response)
        assert 'location' in response
        assert urlparse(response['location']).path == url_path
        # Confirm that the PUT worked.
        doc = Document.objects.get(locale=locale, slug=slug)
        assert doc.title == expected_title
        assert doc.html == data['content']
        if content_case in ('multipart', 'json'):
            rev = doc.current_revision
            assert rev.summary == data['summary']
            assert rev.comment == data['comment']
            assert rev.tags == data['tags']
            assert (set(rev.review_tags.names()) ==
                    set(data['review_tags'].split(',')))


def test_apply_content_experiment_no_experiment(ce_settings, rf):
    """If not under a content experiment, use the original Document."""
    doc = mock.Mock(spec_set=['locale', 'slug'])
    doc.locale = 'en-US'
    doc.slug = 'Other'
    request = rf.get('/%s/docs/%s' % (doc.locale, doc.slug))

    experiment_doc, params = _apply_content_experiment(request, doc)

    assert experiment_doc == doc
    assert params is None


def test_apply_content_experiment_has_experiment(ce_settings, rf):
    """If under a content experiment, return original Document and params."""
    doc = mock.Mock(spec_set=['locale', 'slug'])
    doc.locale = 'en-US'
    doc.slug = 'Original'
    request = rf.get('/%s/docs/%s' % (doc.locale, doc.slug))

    experiment_doc, params = _apply_content_experiment(request, doc)

    assert experiment_doc == doc
    assert params == {
        'id': 'experiment-test',
        'ga_name': 'experiment-test',
        'param': 'v',
        'original_path': '/en-US/docs/Original',
        'variants': {
            'control': 'Original',
            'test': 'Experiment:Test/Variant',
        },
        'selected': None,
        'selection_is_valid': None,
    }


def test_apply_content_experiment_selected_original(ce_settings, rf):
    """If the original is selected as the content experiment, return it."""
    doc = mock.Mock(spec_set=['locale', 'slug'])
    db_doc = mock.Mock(spec_set=['locale', 'slug'])
    doc.locale = db_doc.locale = 'en-US'
    doc.slug = db_doc.slug = 'Original'
    request = rf.get('/%s/docs/%s' % (doc.locale, doc.slug), {'v': 'control'})

    with mock.patch(
            'kuma.wiki.views.document.Document.objects.get',
            return_value=db_doc) as mock_get:
        experiment_doc, params = _apply_content_experiment(request, doc)

    mock_get.assert_called_once_with(locale='en-US', slug='Original')
    assert experiment_doc == db_doc
    assert params['selected'] == 'control'
    assert params['selection_is_valid']


def test_apply_content_experiment_selected_variant(ce_settings, rf):
    """If the variant is selected as the content experiment, return it."""
    doc = mock.Mock(spec_set=['locale', 'slug'])
    db_doc = mock.Mock(spec_set=['locale', 'slug'])
    doc.locale = db_doc.locale = 'en-US'
    doc.slug = 'Original'
    db_doc.slug = 'Experiment:Test/Variant'
    request = rf.get('/%s/docs/%s' % (doc.locale, doc.slug), {'v': 'test'})

    with mock.patch(
            'kuma.wiki.views.document.Document.objects.get',
            return_value=db_doc) as mock_get:
        experiment_doc, params = _apply_content_experiment(request, doc)

    mock_get.assert_called_once_with(locale='en-US',
                                     slug='Experiment:Test/Variant')
    assert experiment_doc == db_doc
    assert params['selected'] == 'test'
    assert params['selection_is_valid']


def test_apply_content_experiment_bad_selection(ce_settings, rf):
    """If the variant is selected as the content experiment, return it."""
    doc = mock.Mock(spec_set=['locale', 'slug'])
    doc.locale = 'en-US'
    doc.slug = 'Original'
    request = rf.get('/%s/docs/%s' % (doc.locale, doc.slug), {'v': 'other'})

    experiment_doc, params = _apply_content_experiment(request, doc)

    assert experiment_doc == doc
    assert params['selected'] is None
    assert not params['selection_is_valid']


def test_apply_content_experiment_valid_selection_no_doc(ce_settings, rf):
    """If the Document for a variant doesn't exist, return the original."""
    doc = mock.Mock(spec_set=['locale', 'slug'])
    doc.locale = 'en-US'
    doc.slug = 'Original'
    request = rf.get('/%s/docs/%s' % (doc.locale, doc.slug), {'v': 'test'})

    with mock.patch(
            'kuma.wiki.views.document.Document.objects.get',
            side_effect=Document.DoesNotExist) as mock_get:
        experiment_doc, params = _apply_content_experiment(request, doc)

    mock_get.assert_called_once_with(locale='en-US',
                                     slug='Experiment:Test/Variant')
    assert experiment_doc == doc
    assert params['selected'] is None
    assert not params['selection_is_valid']


def test_document_banned_ip_can_read(client, root_doc):
    '''Banned IPs are still allowed to read content, just not edit.'''
    ip = '127.0.0.1'
    IPBan.objects.create(ip=ip)
    response = client.get(root_doc.get_absolute_url(), REMOTE_ADDR=ip,
                          HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200


@pytest.mark.parametrize('endpoint', ['document', 'preview'])
def test_kumascript_error_reporting(admin_client, root_doc, ks_toolbox,
                                    endpoint, mock_requests):
    """
    Kumascript reports errors in HTTP headers. Kuma should display the errors
    with appropriate links for both the "wiki.preview" and "wiki.document"
    endpoints.
    """
    ks_settings = dict(
        KUMASCRIPT_TIMEOUT=1.0,
        KUMASCRIPT_MAX_AGE=600,
        KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT=10.0,
        KUMA_DOCUMENT_RENDER_TIMEOUT=180.0
    )
    mock_ks_config = mock.patch('kuma.wiki.kumascript.config', **ks_settings)
    with mock_ks_config:
        mock_requests.post(
            requests_mock.ANY,
            text='HELLO WORLD',
            headers=ks_toolbox.errors_as_headers,
        )
        mock_requests.get(
            requests_mock.ANY,
            **ks_toolbox.macros_response
        )
        if endpoint == 'preview':
            response = admin_client.post(
                reverse('wiki.preview'),
                dict(content='anything truthy'),
                HTTP_HOST=settings.WIKI_HOST
            )
        else:
            with mock.patch('kuma.wiki.models.config', **ks_settings):
                response = admin_client.get(root_doc.get_absolute_url(),
                                            HTTP_HOST=settings.WIKI_HOST)

    assert response.status_code == 200

    response_html = pq(response.content)
    macro_link = ('#kserrors-list a[href="https://github.com/'
                  'mdn/kumascript/blob/master/macros/{}.ejs"]')
    create_link = ('#kserrors-list a[href="https://github.com/'
                   'mdn/kumascript#updating-macros"]')
    assert len(response_html.find(macro_link.format('SomeMacro'))) == 1
    assert len(response_html.find(create_link)) == 1

    assert mock_requests.request_history[0].headers['X-FireLogger'] == '1.2'
    for error in ks_toolbox.errors['logs']:
        assert error['message'] in response.content


@pytest.mark.tags
def test_tags_show_in_document(root_doc, client, wiki_user):
    """Test tags are showing correctly in document view"""
    tags = ('JavaScript', 'AJAX', 'DOM')
    Revision.objects.create(document=root_doc, tags=','.join(tags), creator=wiki_user)
    response = client.get(root_doc.get_absolute_url(),
                          HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200

    page = pq(response.content)
    response_tags = page.find('.tags li a').contents()
    assert len(response_tags) == len(tags)
    # The response tags should be sorted
    assert response_tags == sorted(tags)


@pytest.mark.tags
def test_tags_not_show_while_empty(root_doc, client, wiki_user):
    # Create a revision with no tags
    Revision.objects.create(document=root_doc, tags=','.join([]), creator=wiki_user)

    response = client.get(root_doc.get_absolute_url(),
                          HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200

    page = pq(response.content)
    response_tags = page.find('.tags li a').contents()
    # There should be no tag
    assert len(response_tags) == 0


@pytest.mark.parametrize(
    'params_case',
    ['nothing', 'title-only', 'slug-only', 'title-and-slug', 'missing-title'])
def test_json(doc_hierarchy, client, params_case):
    """Test the wiki.json endpoint."""
    top_doc = doc_hierarchy.top
    bottom_doc = doc_hierarchy.bottom

    expected_tags = sorted(['foo', 'bar', 'baz'])
    expected_review_tags = sorted(['tech', 'editorial'])

    for doc in (top_doc, bottom_doc):
        doc.tags.set(*expected_tags)
        doc.current_revision.review_tags.set(*expected_review_tags)

    params = None
    expected_slug = None
    expected_status_code = 200
    if params_case == 'nothing':
        expected_status_code = 400
    elif params_case == 'title-only':
        expected_slug = top_doc.slug
        params = dict(title=top_doc.title)
    elif params_case == 'slug-only':
        expected_slug = bottom_doc.slug
        params = dict(slug=bottom_doc.slug)
    elif params_case == 'title-and-slug':
        expected_slug = top_doc.slug
        params = dict(title=top_doc.title, slug=bottom_doc.slug)
    else:  # missing title
        expected_status_code = 404
        params = dict(title='nonexistent document title')

    url = reverse('wiki.json')
    with override_switch('application_ACAO', True):
        response = client.get(url, params)

    assert response.status_code == expected_status_code
    if response.status_code == 404:
        assert_no_cache_header(response)
    else:
        assert_shared_cache_header(response)
        assert response['Access-Control-Allow-Origin'] == '*'
    if response.status_code == 200:
        data = json.loads(response.content)
        assert data['slug'] == expected_slug
        assert sorted(data['tags']) == expected_tags
        assert sorted(data['review_tags']) == expected_review_tags


@pytest.mark.parametrize('params_case', ['with-params', 'without-params'])
def test_fallback_to_translation(root_doc, trans_doc, client, params_case):
    """
    If a slug isn't found in the requested locale but is in the default
    locale and if there is a translation of that default-locale document to
    the requested locale, the translation should be served.
    """
    params = '?x=y&x=z' if (params_case == 'with-params') else ''
    url = reverse('wiki.document', args=[root_doc.slug], locale='fr')
    response = client.get(url + params, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert_shared_cache_header(response)
    assert response['Location'].endswith(trans_doc.get_absolute_url() + params)


def test_redirect_with_no_slug(db, client):
    """Bug 775241: Fix exception in redirect for URL with ui-locale"""
    url = '/en-US/docs/en-US/'
    response = client.get(url)
    assert response.status_code == 404
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    'http_method', ['get', 'put', 'delete', 'options', 'head'])
@pytest.mark.parametrize(
    'endpoint', ['wiki.subscribe', 'wiki.subscribe_to_tree'])
def test_watch_405(client, root_doc, endpoint, http_method):
    """Watch document with HTTP non-POST request results in 405."""
    url = reverse(endpoint, args=[root_doc.slug])
    response = getattr(client, http_method)(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    'endpoint', ['wiki.subscribe', 'wiki.subscribe_to_tree'])
def test_watch_login_required(client, root_doc, endpoint):
    """User must be logged-in to subscribe to a document."""
    url = reverse(endpoint, args=[root_doc.slug])
    response = client.post(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert_no_cache_header(response)
    assert response['Location'].endswith(
        reverse('account_login') + '?next=' + quote(url))


@pytest.mark.parametrize(
    'endpoint,event', [('wiki.subscribe', EditDocumentEvent),
                       ('wiki.subscribe_to_tree', EditDocumentInTreeEvent)],
    ids=['subscribe', 'subscribe_to_tree'])
def test_watch_unwatch(user_client, wiki_user, root_doc, endpoint, event):
    """Watch and unwatch a document."""
    url = reverse(endpoint, args=[root_doc.slug])
    # Subscribe
    response = user_client.post(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert_no_cache_header(response)
    assert response['Location'].endswith(
        reverse('wiki.document', args=[root_doc.slug]))
    assert event.is_notifying(wiki_user, root_doc), 'Watch was not created'

    # Unsubscribe
    response = user_client.post(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert_no_cache_header(response)
    assert response['Location'].endswith(
        reverse('wiki.document', args=[root_doc.slug]))
    assert not event.is_notifying(wiki_user, root_doc), \
        'Watch was not destroyed'


def test_deleted_doc_anon(deleted_doc, client):
    """Requesting a deleted doc returns 404"""
    response = client.get(deleted_doc.get_absolute_url(),
                          HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404
    content = response.content.decode(response.charset)
    assert "This document was deleted" not in content
    assert 'Reason for Deletion' not in content


def test_deleted_doc_user(deleted_doc, user_client):
    """Requesting a deleted doc returns 404, deletion message"""
    response = user_client.get(deleted_doc.get_absolute_url(),
                               HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404
    content = response.content.decode(response.charset)
    assert "This document was deleted" not in content
    assert 'Reason for Deletion' not in content
    assert 'Restore this document' not in content
    assert 'Purge this document' not in content


def test_deleted_doc_moderator(deleted_doc, moderator_client):
    """Requesting deleted doc as moderator returns 404 with action buttons."""
    response = moderator_client.get(deleted_doc.get_absolute_url(),
                                    HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404
    content = response.content.decode(response.charset)
    assert 'Reason for Deletion' in content
    full_description = (
        'This document was deleted by'
        ' <a href="/en-US/profiles/moderator">moderator</a>'
        ' on <time datetime="2018-08-21T17:22:00-07:00">'
        'August 21, 2018 at 5:22:00 PM PDT</time>.')
    assert full_description in content
    assert 'Restore this document' in content
    assert 'Purge this document' in content


def test_deleted_doc_no_purge_permdeleted(deleted_doc, wiki_moderator,
                                          moderator_client):
    """Requesting deleted doc without purge perm removes purge button."""
    wiki_moderator.user_permissions.remove(
        Permission.objects.get(codename='purge_document'))
    response = moderator_client.get(deleted_doc.get_absolute_url(),
                                    HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404
    content = response.content.decode(response.charset)
    assert 'Reason for Deletion' in content
    full_description = (
        'This document was deleted by'
        ' <a href="/en-US/profiles/moderator">moderator</a>'
        ' on <time datetime="2018-08-21T17:22:00-07:00">'
        'August 21, 2018 at 5:22:00 PM PDT</time>.')
    assert full_description in content
    assert 'Restore this document' in content
    assert 'Purge this document' not in content


@pytest.mark.parametrize('case', ('DOMAIN', 'WIKI_HOST'))
def test_redirect_suppression(client, settings, root_doc, redirect_doc, case):
    """The document view shouldn't redirect when passed redirect=no."""
    host = getattr(settings, case)
    url = redirect_doc.get_absolute_url()
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 301
    response = client.get(url + '?redirect=no', HTTP_HOST=host)
    assert response.status_code == 200


@pytest.mark.parametrize(
    'href', ['//davidwalsh.name', 'http://davidwalsh.name'])
@mock.patch('kuma.wiki.kumascript.get')
def test_redirects_only_internal(mock_kumascript_get, constance_config,
                                 wiki_user, client, href):
    """Ensures redirects cannot be used to link to other sites"""
    constance_config.KUMASCRIPT_TIMEOUT = 1
    redirect_doc = Document.objects.create(
        locale='en-US', slug='Redirection', title='External Redirect Document')
    Revision.objects.create(
        document=redirect_doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {'href': href, 'title': 'DWB'},
        title='External Redirect Document',
        created=datetime(2018, 4, 18, 12, 15))
    mock_kumascript_get.return_value = (redirect_doc.html, None)
    url = redirect_doc.get_absolute_url()
    response = client.get(url, follow=True, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert not response.redirect_chain
    content = response.content.decode(response.charset)
    body = pq(content).find('#wikiArticle')
    assert body.text() == 'REDIRECT DWB'
    assert body.find('a[href="{}"]'.format(href))


@mock.patch('kuma.wiki.kumascript.get')
def test_self_redirect_supression(mock_kumascript_get, constance_config,
                                  wiki_user, client):
    """The document view shouldn't redirect to itself."""
    constance_config.KUMASCRIPT_TIMEOUT = 1
    redirect_doc = Document.objects.create(
        locale='en-US', slug='Redirection', title='Self Redirect Document')
    url = redirect_doc.get_absolute_url()
    Revision.objects.create(
        document=redirect_doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {'href': url, 'title': 'Self Redirection'},
        title='Self Redirect Document',
        created=datetime(2018, 4, 19, 12, 15))
    mock_kumascript_get.return_value = (redirect_doc.html, None)
    response = client.get(url, follow=True, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert not response.redirect_chain
    content = response.content.decode(response.charset)
    body = pq(content).find('#wikiArticle')
    assert body.text() == 'REDIRECT Self Redirection'
    assert body.find('a[href="{}"][class="redirect"]'.format(url))


@pytest.mark.parametrize('locales,expected_results',
                         HREFLANG_TEST_CASES.values(),
                         ids=tuple(HREFLANG_TEST_CASES.keys()))
def test_hreflang(client, root_doc, locales, expected_results):
    docs = [
        Document.objects.create(
            locale=locale,
            slug='Root',
            title='Root Document',
            rendered_html='<p>...</p>',
            parent=root_doc
        ) for locale in locales
    ]
    for doc, expected_result in zip(docs, expected_results):
        url = doc.get_absolute_url()
        response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200, url
        html = pq(response.content.decode(response.charset))
        assert html.attr('lang') == expected_result
        assert html.find('head > link[hreflang="{}"][href$="{}"]'.format(
            expected_result, url))


@pytest.mark.parametrize(
    'param,status',
    (('utm_source=docs.com', 200),
     ('redirect=no', 200),
     ('nocreate=1', 200),
     ('edit_links=1', 301),
     ('include=1', 301),
     ('macros=1', 301),
     ('nomacros=1', 301),
     ('raw=1', 301),
     ('section=junk', 301),
     ('summary=1', 301)))
@mock.patch('kuma.wiki.kumascript.get')
@mock.patch('kuma.wiki.templatetags.ssr.server_side_render')
def test_wiki_only_query_params(mock_ssr, mock_kumascript_get, constance_config,
                                client, root_doc, param, status):
    """
    The document view should ensure the wiki domain when using specific query
    parameters.
    """
    constance_config.KUMASCRIPT_TIMEOUT = 1
    # For the purpose of this test, we don't care about the content of the
    # document page, so let's explicitly mock the "server_side_render" call.
    mock_ssr.return_value = '<div></div>'
    mock_kumascript_get.return_value = (root_doc.html, None)
    url = root_doc.get_absolute_url() + '?{}'.format(param)
    response = client.get(url)
    assert response.status_code == status
    if status == 301:
        assert_redirect_to_wiki(response, url)
