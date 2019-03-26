from functools import partial

import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse as core_reverse
from kuma.users.templatetags.jinja_helpers import gravatar_url
from kuma.wiki.templatetags.jinja_helpers import absolutify


reverse = partial(core_reverse, urlconf='kuma.urls_beta')


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
def test_doc_api_disallowed_methods(client, api_settings, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse('api.v1.doc', args=['en-US', 'Web/CSS'])
    response = getattr(client, http_method)(url,
                                            HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 405
    assert_no_cache_header(response)


def test_doc_api_404(client, api_settings, root_doc):
    """We get a 404 if we ask for a document that does not exist."""
    url = reverse('api.v1.doc', args=['en-US', 'NoSuchPage'])
    response = client.get(url, HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 404
    assert_no_cache_header(response)


def test_doc_api(client, api_settings, trans_doc):
    """On success we get document details in a JSON response."""
    url = reverse('api.v1.doc', args=[trans_doc.locale, trans_doc.slug])
    response = client.get(url, HTTP_HOST=api_settings.BETA_HOST)
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
    assert data['editURL'] == absolutify(trans_doc.get_edit_url(),
                                         for_wiki_site=True)
    assert data['bodyHTML'] == trans_doc.get_body_html()
    assert data['quickLinksHTML'] == trans_doc.get_quick_links_html()
    assert data['tocHTML'] == trans_doc.get_toc_html()
    assert data['translations'] == [{
        'locale': 'en-US',
        'title': 'Root Document',
        'url': '/en-US/docs/Root'
    }]


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
def test_whoami_disallowed_methods(client, api_settings, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse('api.v1.whoami')
    response = getattr(client, http_method)(url,
                                            HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.parametrize('timezone', ('US/Eastern', 'US/Pacific'))
def test_whoami_anonymous(client, api_settings, timezone):
    """Test response for anonymous users."""
    api_settings.TIME_ZONE = timezone
    url = reverse('api.v1.whoami')
    response = client.get(url, HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 200
    assert response['content-type'] == 'application/json'
    assert response.json() == {
        'username': None,
        'timezone': timezone,
        'is_authenticated': False,
        'is_staff': False,
        'is_superuser': False,
        'is_beta_tester': False,
        'gravatar_url': {
            'small': None,
            'large': None,
        }
    }
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    'timezone,is_staff,is_superuser,is_beta_tester',
    [('US/Eastern', False, False, False),
     ('US/Pacific', True, True, True)],
    ids=('muggle', 'wizard'))
def test_whoami(user_client, api_settings, wiki_user, beta_testers_group,
                timezone, is_staff, is_superuser, is_beta_tester):
    """Test responses for logged-in users."""
    wiki_user.timezone = timezone
    wiki_user.is_staff = is_staff
    wiki_user.is_superuser = is_superuser
    wiki_user.is_staff = is_staff
    if is_beta_tester:
        wiki_user.groups.add(beta_testers_group)
    wiki_user.save()
    url = reverse('api.v1.whoami')
    response = user_client.get(url, HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 200
    assert response['content-type'] == 'application/json'
    assert response.json() == {
        'username': wiki_user.username,
        'timezone': timezone,
        'is_authenticated': True,
        'is_staff': is_staff,
        'is_superuser': is_superuser,
        'is_beta_tester': is_beta_tester,
        'gravatar_url': {
            'small': gravatar_url(wiki_user.email, size=50),
            'large': gravatar_url(wiki_user.email, size=200),
        }
    }
    assert_no_cache_header(response)
