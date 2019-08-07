import json

import pytest
from django.conf import settings
from django.utils.six.moves.urllib.parse import urlencode
from waffle.testutils import override_switch

from kuma.core.tests import assert_shared_cache_header
from kuma.core.urlresolvers import reverse


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
@pytest.mark.parametrize(
    'endpoint', ['ckeditor_config', 'autosuggest_documents'])
def test_disallowed_methods(db, client, http_method, endpoint):
    """HTTP methods other than GET & HEAD are not allowed."""
    url = reverse('wiki.{}'.format(endpoint))
    response = getattr(client, http_method)(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 405
    assert_shared_cache_header(response)


def test_ckeditor_config(db, client):
    response = client.get(reverse('wiki.ckeditor_config'),
                          HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response['Content-Type'] == 'application/x-javascript'
    assert 'wiki/ckeditor_config.js' in [t.name for t in response.templates]


@pytest.mark.parametrize('term', [None, 'doc'])
@pytest.mark.parametrize(
    'locale_case',
    ['all-locales', 'current-locale',
     'non-english-locale', 'exclude-current-locale'])
def test_autosuggest(client, redirect_doc, doc_hierarchy, locale_case, term):
    params = {}
    expected_status_code = 200
    if term:
        params.update(term=term)
    else:
        expected_status_code = 400
    if locale_case == 'non-english-locale':
        params.update(locale='it')
        expected_titles = set(('Superiore Documento',))
    elif locale_case == 'current-locale':
        params.update(current_locale='true')
        # The root document is pulled-in by the redirect_doc fixture.
        expected_titles = set(('Root Document', 'Top Document',
                               'Middle-Top Document', 'Middle-Bottom Document',
                               'Bottom Document'))
    elif locale_case == 'exclude-current-locale':
        params.update(exclude_current_locale='true')
        expected_titles = set(('Haut Document', 'Superiore Documento'))
    else:  # All locales
        # The root document is pulled-in by the redirect_doc fixture.
        expected_titles = set(('Root Document', 'Top Document',
                               'Haut Document', 'Superiore Documento',
                               'Middle-Top Document', 'Middle-Bottom Document',
                               'Bottom Document'))

    url = reverse('wiki.autosuggest_documents')
    if params:
        url += '?{}'.format(urlencode(params))
    with override_switch('application_ACAO', True):
        response = client.get(url)
    assert response.status_code == expected_status_code
    assert_shared_cache_header(response)
    assert 'Access-Control-Allow-Origin' in response
    assert response['Access-Control-Allow-Origin'] == '*'
    if expected_status_code == 200:
        assert response['Content-Type'] == 'application/json'
        data = json.loads(response.content)
        assert set(item['title'] for item in data) == expected_titles
