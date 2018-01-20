"""
Tests for kuma/wiki/views/document.py

Legacy tests are in test_views.py.
"""
import json
import base64
from datetime import datetime
from collections import namedtuple

import mock
import pytest
import requests_mock
from pyquery import PyQuery as pq

from kuma.core.models import IPBan
from kuma.core.urlresolvers import reverse
from kuma.authkeys.models import Key
from kuma.wiki.models import Document, Revision
from kuma.wiki.views.utils import calculate_etag
from kuma.wiki.views.document import _apply_content_experiment

from django.utils.encoding import smart_str
from django.utils.six.moves.urllib.parse import urlparse
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart


AuthKey = namedtuple('AuthKey', 'key header')


SECTION1 = '<h3 id="S1">Section 1</h3><p>This is a page. Deal with it.</p>'
SECTION2 = '<h3 id="S2">Section 2</h3><p>This is a page. Deal with it.</p>'
SECTION3 = '<h3 id="S3">Section 3</h3><p>This is a page. Deal with it.</p>'
SECTIONS = SECTION1 + SECTION2 + SECTION3
SECTION_CASE_TO_DETAILS = {
    'no-section': (None, SECTIONS),
    'section': ('S1', SECTION1),
    'another-section': ('S3', SECTION3),
    'non-existent-section': ('S99', '')
}


def get_content(content_case, settings, data):
    if content_case == 'multipart':
        return MULTIPART_CONTENT, encode_multipart(BOUNDARY, data)

    if content_case == 'json':
        content_type = 'application/json'
        mod_data = json.dumps(data)
    elif content_case == 'html-fragment':
        content_type = 'text/html'
        mod_data = data['content']
    elif content_case == 'html':
        content_type = 'text/html'
        mod_data = """
            <html>
                <head>
                    <title>%(title)s</title>
                </head>
                <body>%(content)s</body>
            </html>
        """ % data

    encoded_data = smart_str(mod_data, encoding=settings.DEFAULT_CHARSET)

    return content_type, encoded_data


@pytest.fixture
def sectioned_root_doc(wiki_user):
    """
    A newly-created top-level English document with sections.
    """
    root_doc = Document.objects.create(
        locale='en-US', slug='Root', title='Sectioned Root Document')
    Revision.objects.create(
        document=root_doc,
        creator=wiki_user,
        content=SECTIONS,
        title='Sectioned Root Document',
        created=datetime(2018, 1, 20, 12, 15))
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
    header = 'Basic %s' % base64.encodestring(auth)
    return AuthKey(key=key, header=header)


@pytest.mark.parametrize('method', ('GET', 'HEAD'))
@pytest.mark.parametrize('if_none_match', (None, 'match', 'mismatch'))
@pytest.mark.parametrize(
    'section_case',
    ('no-section', 'section', 'another-section', 'non-existent-section')
)
def test_api_safe(client, sectioned_root_doc, section_case, if_none_match,
                  method):
    """
    Test GET & HEAD on wiki.document_api endpoint.
    """
    section_id, exp_content = SECTION_CASE_TO_DETAILS[section_case]

    url = sectioned_root_doc.get_absolute_url() + '$api'

    if section_id:
        url += '?section={}'.format(section_id)

    headers = {}
    if if_none_match == 'match':
        headers['HTTP_IF_NONE_MATCH'] = calculate_etag(
            sectioned_root_doc.get_html(section_id)
        )
    elif if_none_match == 'mismatch':
        headers['HTTP_IF_NONE_MATCH'] = 'ABC'

    response = getattr(client, method.lower())(url, **headers)

    if if_none_match == 'match':
        exp_content = ''
        assert response.status_code == 304
    else:
        assert response.status_code == 200
        assert 'etag' in response
        assert 'x-kuma-revision' in response
        assert 'last-modified' not in response
        assert response['etag'] == '"{}"'.format(calculate_etag(exp_content))
        assert (response['x-kuma-revision'] ==
                str(sectioned_root_doc.current_revision_id))

    if method == 'GET':
        assert response.content == exp_content


def test_api_put_forbidden_when_no_authkey(client, wiki_user, root_doc):
    """
    A PUT to the wiki.document_api endpoint should forbid access without
    an authkey, even for logged-in users.
    """
    url = root_doc.get_absolute_url() + '$api'

    response = client.put(url)
    assert response.status_code == 403

    # Even logged-in users without an authkey should be forbidden.
    wiki_user.set_password('password')
    wiki_user.save()

    assert client.login(username=wiki_user.username, password='password')

    response = client.put(url)
    assert response.status_code == 403


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
        HTTP_AUTHORIZATION=authkey.header
    )
    assert response.status_code == 400


def test_api_put_authkey_tracking(settings, client, authkey):
    """
    Revisions modified by PUT API should track the auth key used
    """
    url = '/en-US/docs/foobar$api'
    data = dict(
        title="Foobar, The Document",
        content='<p>Hello, I am foobar.</p>',
    )
    content_type, encoded_data = get_content('json', settings, data)
    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        HTTP_AUTHORIZATION=authkey.header
    )
    assert response.status_code == 201
    last_log = authkey.key.history.order_by('-pk').all()[0]
    assert last_log.action == 'created'

    data['title'] = 'Foobar, The New Document'
    content_type, encoded_data = get_content('json', settings, data)
    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        HTTP_AUTHORIZATION=authkey.header
    )
    assert response.status_code == 205
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
def test_api_put_existing(settings, client, sectioned_root_doc, authkey,
                          section_case, content_case, if_match):
    """
    A PUT to the wiki.document_api endpoint should allow the modification
    of an existing document's content.
    """
    orig_rev_id = sectioned_root_doc.current_revision_id
    section_id, section_content = SECTION_CASE_TO_DETAILS[section_case]

    url = sectioned_root_doc.get_absolute_url() + '$api'

    if section_id:
        url += '?section={}'.format(section_id)

    headers = dict(HTTP_AUTHORIZATION=authkey.header)
    if if_match == 'match':
        headers['HTTP_IF_MATCH'] = calculate_etag(
            sectioned_root_doc.get_html(section_id)
        )
    elif if_match == 'mismatch':
        headers['HTTP_IF_MATCH'] = 'ABC'

    data = dict(
        comment="I like this document.",
        title="New Sectioned Root Document",
        summary="An edited sectioned root document.",
        content="<p>This is an edit.</p>",
        tags="tagA,tagB,tagC",
        review_tags="editorial,technical",
    )

    content_type, encoded_data = get_content(content_case, settings, data)

    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        **headers
    )

    if content_case == 'html-fragment':
        expected_title = sectioned_root_doc.title
    else:
        expected_title = data['title']

    if section_content:
        expected_content = SECTIONS.replace(section_content, data['content'])
    else:
        expected_content = SECTIONS

    if if_match == 'mismatch':
        assert response.status_code == 412
    else:
        assert response.status_code == 205
        # Confirm that the PUT worked.
        sectioned_root_doc.refresh_from_db()
        assert sectioned_root_doc.current_revision_id != orig_rev_id
        assert sectioned_root_doc.title == expected_title
        assert sectioned_root_doc.html == expected_content
        if content_case in ('multipart', 'json'):
            rev = sectioned_root_doc.current_revision
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
        content=SECTIONS,
        tags="tagA,tagB,tagC",
        review_tags="editorial,technical",
    )

    content_type, encoded_data = get_content(content_case, settings, data)

    response = client.put(
        url,
        data=encoded_data,
        content_type=content_type,
        HTTP_AUTHORIZATION=authkey.header,
    )

    if content_case == 'html-fragment':
        expected_title = slug
    else:
        expected_title = data['title']

    if slug_case == 'nonexistent-parent':
        assert response.status_code == 404
    else:
        assert response.status_code == 201
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


def test_conditional_get(settings, client, root_doc):
    """
    Test conditional GET to document view (ETag only currently).
    """
    url = root_doc.get_absolute_url() + '$api'

    response = client.get(url)

    assert response.status_code == 200
    assert 'etag' in response
    assert 'last-modified' not in response
    # Ensure the ETag value is strong. It should be
    # based on the entire content of the response.
    assert response['etag'] == '"{}"'.format(calculate_etag(response.content))

    response = client.get(url, HTTP_IF_NONE_MATCH=response['etag'])

    assert response.status_code == 304
    assert 'etag' in response
    assert 'last-modified' not in response


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
    response = client.get(root_doc.get_absolute_url(), REMOTE_ADDR=ip)
    assert response.status_code == 200


@pytest.mark.parametrize('endpoint', ['document', 'preview'])
def test_kumascript_error_reporting(admin_client, root_doc, ks_toolbox,
                                    endpoint):
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
    mock_requests = requests_mock.Mocker()
    mock_ks_config = mock.patch('kuma.wiki.kumascript.config', **ks_settings)
    with mock_ks_config, mock_requests:
        if endpoint == 'preview':
            mock_requests.post(
                requests_mock.ANY,
                text='HELLO WORLD',
                headers=ks_toolbox.errors_as_headers,
            )
            mock_requests.get(
                requests_mock.ANY,
                **ks_toolbox.macros_response
            )
            response = admin_client.post(
                reverse('wiki.preview', locale=root_doc.locale),
                dict(content='anything truthy')
            )
        else:
            mock_requests.get(
                requests_mock.ANY,
                [
                    dict(
                        text='HELLO WORLD',
                        headers=ks_toolbox.errors_as_headers
                    ),
                    ks_toolbox.macros_response,
                ]
            )
            with mock.patch('kuma.wiki.models.config', **ks_settings):
                response = admin_client.get(root_doc.get_absolute_url())

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
    response = client.get(root_doc.get_absolute_url())
    assert response.status_code == 200

    page = pq(response.content)
    response_tags = page.find('.tags li a').contents()
    assert len(response_tags) == len(tags)
    # The response tags should be sorted
    assert response_tags == sorted(tags)
