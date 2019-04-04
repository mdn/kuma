from datetime import datetime
from functools import partial

import mock
import pytest

from kuma.api.v1.views import document_api_data
from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse as core_reverse
from kuma.users.templatetags.jinja_helpers import gravatar_url
from kuma.wiki.constants import REDIRECT_CONTENT
from kuma.wiki.models import Document, Revision
from kuma.wiki.templatetags.jinja_helpers import absolutify


reverse = partial(core_reverse, urlconf='kuma.urls_beta')


@pytest.fixture
def redirect_to_home_page(wiki_user):
    """
    A top-level English redirect document that redirects to the home page.
    """
    redirect_doc = Document.objects.create(
        locale='en-US', slug='GoHome', title='Redirect to Home Page')
    Revision.objects.create(
        document=redirect_doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {
            'href': '/',
            'title': 'MDN Web Docs',
        },
        title='Redirect to Home Page',
        created=datetime(2015, 7, 4, 11, 15))
    return redirect_doc


@pytest.fixture
def redirect_to_macros_dashboard(wiki_user):
    """
    A top-level English redirect document that redirects to the home page.
    """
    redirect_doc = Document.objects.create(
        locale='en-US', slug='GoMacros', title='Redirect to Macros Dashboard')
    Revision.objects.create(
        document=redirect_doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {
            'href': '/en-US/dashboards/macros',
            'title': 'Active macros | MDN',
        },
        title='Redirect to Macros Dashboard',
        created=datetime(2017, 5, 24, 12, 15))
    return redirect_doc


@pytest.fixture
def redirect_to_redirect_doc(wiki_user_2, redirect_doc):
    """
    A top-level English redirect document that redirects to the redirect_doc.
    """
    r2r_doc = Document.objects.create(
        locale='en-US', slug='DoubleRedirect', title='Double Redirect Document')
    Revision.objects.create(
        document=r2r_doc,
        creator=wiki_user_2,
        content=REDIRECT_CONTENT % {
            'href': reverse('wiki.document', args=(redirect_doc.slug,)),
            'title': redirect_doc.title,
        },
        title='Double Redirect Document',
        created=datetime(2016, 4, 17, 12, 15))
    return r2r_doc


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


@mock.patch('kuma.wiki.jobs.DocumentContributorsJob.fetch_on_miss', True)
def test_doc_api(client, api_settings, trans_doc, cleared_cacheback_cache):
    """On success we get document details in a JSON response."""

    # The fetch_on_miss mock and the cleared_cacheback_cache fixture
    # are here to ensure that we don't get an old cached value for
    # the contributors property, and also that we don't use []
    # while a celery job is running.
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
        'language': 'English (US)',
        'localizedLanguage': u'Anglais am\u00e9ricain',
        'title': 'Root Document',
        'url': '/en-US/docs/Root'
    }]
    assert data['contributors'] == ['wiki_user']
    assert data['lastModified'] == '2017-04-14T12:20:00'
    assert data['lastModifiedBy'] == 'wiki_user'

    # Also ensure that we get exactly the same data by calling
    # the document_api_data() function directly
    data2 = document_api_data(trans_doc)
    assert data == data2


@pytest.mark.parametrize('case', ('normal',
                                  'redirect',
                                  'redirect-to-redirect',
                                  'redirect-to-home-page',
                                  'redirect-to-wiki'))
def test_document_api_data(settings, root_doc, trans_doc, redirect_doc,
                           redirect_to_redirect_doc, redirect_to_home_page,
                           redirect_to_macros_dashboard, case):
    expected_data = {
        'absoluteURL': root_doc.get_absolute_url(),
        'bodyHTML': root_doc.get_body_html(),
        'contributors': ['wiki_user'],
        'editURL': absolutify(root_doc.get_edit_url(), for_wiki_site=True),
        'id': root_doc.id,
        'language': root_doc.language,
        'lastModified': '2017-04-14T12:15:00',
        'lastModifiedBy': 'wiki_user',
        'locale': root_doc.locale,
        'parents': [],
        'quickLinksHTML': root_doc.get_quick_links_html(),
        'redirectURL': None,
        'slug': root_doc.slug,
        'summary': root_doc.get_summary_html(),
        'title': root_doc.title,
        'tocHTML': root_doc.get_toc_html(),
        'translations': [
            {
                'language': trans_doc.language,
                'localizedLanguage': 'French',
                'locale': trans_doc.locale,
                'url': trans_doc.get_absolute_url(),
                'title': trans_doc.title
            }
        ]
    }
    if case == 'normal':
        doc = root_doc
    elif case == 'redirect':
        doc = redirect_doc
    elif case == 'redirect-to-redirect':
        doc = redirect_to_redirect_doc
    else:
        expected_data = {
            'absoluteURL': None,
            'bodyHTML': None,
            'contributors': None,
            'editURL': None,
            'id': None,
            'language': None,
            'lastModified': None,
            'lastModifiedBy': None,
            'locale': None,
            'parents': None,
            'quickLinksHTML': None,
            'slug': None,
            'summary': None,
            'title': None,
            'tocHTML': None,
            'translations': None
        }
        if case == 'redirect-to-home-page':
            doc = redirect_to_home_page
            expected_data['redirectURL'] = '/'
        else:
            doc = redirect_to_macros_dashboard
            expected_data['redirectURL'] = (
                settings.WIKI_SITE_URL + '/en-US/dashboards/macros')
    assert document_api_data(doc, ensure_contributors=True) == expected_data


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
