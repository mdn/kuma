from __future__ import unicode_literals

import pytest
from waffle.models import Flag, Sample, Switch

from kuma.api.v1.views import (document_api_data, get_content_based_redirect,
                               get_s3_key)
from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.users.templatetags.jinja_helpers import gravatar_url
from kuma.wiki.jobs import DocumentContributorsJob
from kuma.wiki.templatetags.jinja_helpers import absolutify


def test_get_s3_key(root_doc):
    locale, slug = root_doc.locale, root_doc.slug
    expected_key = 'api/v1/doc/{}/{}'.format(locale, slug)
    assert (
        get_s3_key(root_doc) == get_s3_key(locale=locale, slug=slug) ==
        expected_key
    )
    assert (
        get_s3_key(root_doc, prefix_with_forward_slash=True) ==
        get_s3_key(locale=locale, slug=slug, prefix_with_forward_slash=True) ==
        '/' + expected_key
    )


@pytest.mark.parametrize('case', ('normal',
                                  'redirect',
                                  'redirect-to-self',
                                  'redirect-to-home',
                                  'redirect-to-wiki'))
def test_get_content_based_redirect(root_doc, redirect_doc, redirect_to_self,
                                    redirect_to_home, redirect_to_macros, case):
    if case == 'normal':
        doc = root_doc
        expected = None
    elif case == 'redirect':
        doc = redirect_doc
        expected = (get_s3_key(root_doc, prefix_with_forward_slash=True), True)
    elif case == 'redirect-to-self':
        doc = redirect_to_self
        expected = None
    elif case == 'redirect-to-home':
        doc = redirect_to_home
        expected = ('/en-US/', False)
    else:
        doc = redirect_to_macros
        expected = (
            absolutify('/en-US/dashboards/macros', for_wiki_site=True), False)
    assert get_content_based_redirect(doc) == expected


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


@pytest.mark.parametrize('ensure_contributors', (True, False))
def test_doc_api(client, api_settings, trans_doc, cleared_cacheback_cache,
                 ensure_contributors):
    """On success we get document details in a JSON response."""
    if ensure_contributors:
        # Pre-populate the cache for the call to document_api_data()
        # made within the view that serves the "api.v1.doc" endpoint.
        DocumentContributorsJob().refresh(trans_doc.pk)

    url = reverse('api.v1.doc', args=[trans_doc.locale, trans_doc.slug])
    response = client.get(url, HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 200
    assert_no_cache_header(response)

    data = response.json()
    assert data['documentData']
    assert data['redirectURL'] is None
    doc_data = data['documentData']
    assert doc_data['locale'] == trans_doc.locale
    assert doc_data['slug'] == trans_doc.slug
    assert doc_data['id'] == trans_doc.id
    assert doc_data['title'] == trans_doc.title
    assert doc_data['language'] == trans_doc.language
    assert doc_data['hrefLang'] == 'fr'
    assert doc_data['absoluteURL'] == trans_doc.get_absolute_url()
    assert doc_data['editURL'] == absolutify(trans_doc.get_edit_url(),
                                             for_wiki_site=True)
    assert doc_data['translateURL'] is None
    assert doc_data['bodyHTML'] == trans_doc.get_body_html()
    assert doc_data['quickLinksHTML'] == trans_doc.get_quick_links_html()
    assert doc_data['tocHTML'] == trans_doc.get_toc_html()
    assert doc_data['translations'] == [{
        'locale': 'en-US',
        'language': 'English (US)',
        'hrefLang': 'en',
        'localizedLanguage': u'Anglais am\u00e9ricain',
        'title': 'Root Document',
        'url': '/en-US/docs/Root'
    }]
    assert doc_data['contributors'] == (
        ['wiki_user'] if ensure_contributors else [])
    assert doc_data['lastModified'] == '2017-04-14T12:20:00'
    assert doc_data['lastModifiedBy'] == 'wiki_user'

    # Clear the cache for a clean slate when calling document_api_data().
    DocumentContributorsJob().delete(trans_doc.pk)

    # Also ensure that we get exactly the same data by calling
    # the document_api_data() function directly
    assert data == document_api_data(
        trans_doc, ensure_contributors=ensure_contributors)


@pytest.mark.parametrize('ensure_contributors', (True, False))
def test_doc_api_for_redirect_to_doc(client, api_settings, root_doc,
                                     redirect_doc, cleared_cacheback_cache,
                                     ensure_contributors):
    """
    Test the document API when we're requesting data for a document that
    redirects to another document.
    """
    if ensure_contributors:
        # Pre-populate the cache for the call to document_api_data()
        # made within the view that serves the "api.v1.doc" endpoint.
        DocumentContributorsJob().refresh(root_doc.pk)

    url = reverse('api.v1.doc', args=[redirect_doc.locale, redirect_doc.slug])
    response = client.get(url, HTTP_HOST=api_settings.BETA_HOST, follow=True)
    assert response.status_code == 200
    assert_no_cache_header(response)

    data = response.json()
    assert data['documentData']
    assert data['redirectURL'] is None
    doc_data = data['documentData']
    assert doc_data['locale'] == root_doc.locale
    assert doc_data['slug'] == root_doc.slug
    assert doc_data['id'] == root_doc.id
    assert doc_data['title'] == root_doc.title
    assert doc_data['language'] == root_doc.language
    assert doc_data['hrefLang'] == 'en'
    assert doc_data['absoluteURL'] == root_doc.get_absolute_url()
    assert doc_data['editURL'] == absolutify(root_doc.get_edit_url(),
                                             for_wiki_site=True)
    assert doc_data['translateURL'] == absolutify(
        reverse(
            'wiki.select_locale',
            args=(root_doc.slug,),
            locale=root_doc.locale,
        ),
        for_wiki_site=True
    )
    assert doc_data['bodyHTML'] == root_doc.get_body_html()
    assert doc_data['quickLinksHTML'] == root_doc.get_quick_links_html()
    assert doc_data['tocHTML'] == root_doc.get_toc_html()
    assert doc_data['translations'] == []
    assert doc_data['contributors'] == (
        ['wiki_user'] if ensure_contributors else [])
    assert doc_data['lastModified'] == '2017-04-14T12:15:00'
    assert doc_data['lastModifiedBy'] == 'wiki_user'

    # Clear the cache for a clean slate when calling document_api_data().
    DocumentContributorsJob().delete(root_doc.pk)

    # Also ensure that we get exactly the same data by calling
    # the document_api_data() function directly
    assert data == document_api_data(
        root_doc, ensure_contributors=ensure_contributors)


@pytest.mark.parametrize('case', ('redirect-to-home', 'redirect-to-other'))
def test_doc_api_for_redirect_to_non_doc(client, api_settings, redirect_to_home,
                                         redirect_to_macros, case):
    """
    Test the document API when we're requesting data for a document that
    redirects to a non-document page (either the home page or another).
    """
    if case == 'redirect-to-home':
        doc = redirect_to_home
        expected_redirect_url = '/en-US/'
    else:
        doc = redirect_to_macros
        expected_redirect_url = absolutify('/en-US/dashboards/macros',
                                           for_wiki_site=True)
    url = reverse('api.v1.doc', args=[doc.locale, doc.slug])
    response = client.get(url, HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 200
    assert_no_cache_header(response)

    data = response.json()
    assert data['documentData'] is None
    assert data['redirectURL'] == expected_redirect_url

    # Also ensure that we get exactly the same data by calling
    # the document_api_data() function directly
    assert data == document_api_data(redirect_url=expected_redirect_url)


@pytest.mark.parametrize(
    'http_method', ['put', 'post', 'delete', 'options', 'head'])
def test_whoami_disallowed_methods(client, api_settings, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse('api.v1.whoami')
    response = getattr(client, http_method)(url,
                                            HTTP_HOST=api_settings.BETA_HOST)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.django_db
@pytest.mark.parametrize('timezone', ('US/Eastern', 'US/Pacific'))
def test_whoami_anonymous(client, api_settings, timezone):
    """Test response for anonymous users."""
    # Create some fake waffle objects
    Flag.objects.create(name='section_edit', authenticated=True)
    Flag.objects.create(name='flag_all', everyone=True)
    Flag.objects.create(name='flag_none', percent=0)
    Switch.objects.create(name="switch_on", active=True)
    Switch.objects.create(name="switch_off", active=False)
    Sample.objects.create(name="sample_never", percent=0)
    Sample.objects.create(name="sample_always", percent=100)

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
        },
        'waffle': {
            'flags': {
                'section_edit': False,
                'flag_all': True,
                'flag_none': False,
            },
            'switches': {
                'switch_on': True,
                'switch_off': False
            },
            'samples': {
                'sample_always': True,
                'sample_never': False
            }
        }
    }
    assert_no_cache_header(response)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'timezone,is_staff,is_superuser,is_beta_tester',
    [('US/Eastern', False, False, False),
     ('US/Pacific', True, True, True)],
    ids=('muggle', 'wizard'))
def test_whoami(user_client, api_settings, wiki_user, beta_testers_group,
                timezone, is_staff, is_superuser, is_beta_tester):
    """Test responses for logged-in users."""
    # Create some fake waffle objects
    Flag.objects.create(name='section_edit', authenticated=True)
    Flag.objects.create(name='flag_all', everyone=True)
    Flag.objects.create(name='flag_none', percent=0, superusers=False)
    Switch.objects.create(name="switch_on", active=True)
    Switch.objects.create(name="switch_off", active=False)
    Sample.objects.create(name="sample_never", percent=0)
    Sample.objects.create(name="sample_always", percent=100)

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
        },
        'waffle': {
            'flags': {
                'section_edit': True,
                'flag_all': True,
                'flag_none': False,
            },
            'switches': {
                'switch_on': True,
                'switch_off': False
            },
            'samples': {
                'sample_always': True,
                'sample_never': False
            }
        }
    }
    assert_no_cache_header(response)
