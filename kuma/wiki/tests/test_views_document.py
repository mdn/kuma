"""
Tests for kuma/wiki/views/document.py

Legacy tests are in test_views.py.
"""
import mock
import pytest
import requests_mock
from pyquery import PyQuery as pq

from kuma.wiki.models import Document
from kuma.core.urlresolvers import reverse
from kuma.wiki.views.document import _apply_content_experiment


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
