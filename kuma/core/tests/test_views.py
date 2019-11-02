

import logging

import mock
import pytest
from django.conf import settings
from django.core import mail
from django.test import override_settings
from django.utils.log import AdminEmailHandler
from pyquery import PyQuery as pq
from ratelimit.exceptions import Ratelimited
from soapbox.models import Message
from waffle.models import Flag

from . import (assert_no_cache_header, assert_shared_cache_header,
               KumaTestCase)
from ..urlresolvers import reverse
from ..views import handler500


@pytest.fixture()
def sitemaps(db, settings, tmpdir):
    media_dir = tmpdir.mkdir('media')
    locale_dir = media_dir.mkdir('sitemaps').mkdir('en-US')
    sitemap_file = media_dir.join('sitemap.xml')
    locale_file = locale_dir.join('sitemap.xml')
    sitemap_file.write_text(u"""
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://localhost:8000/sitemaps/en-US/sitemap.xml</loc>
    <lastmod>2017-09-06T23:24:37+00:00</lastmod>
  </sitemap>
</sitemapindex>""", 'utf8')
    locale_file.write_text(u"""
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/en-US/docs/foobar</loc>
    <lastmod>2013-06-06</lastmod>
   </url>
</urlset>""", 'utf8')
    return {
        'tmpdir': media_dir,
        'index': sitemap_file.read_text('utf8'),
        'locales': {
            'en-US': locale_file.read_text('utf8')
        }
    }


@override_settings(
    DEBUG=False,
    DEBUG_PROPAGATE_EXCEPTIONS=False,
    ADMINS=(('admin', 'admin@example.com'),),
    ROOT_URLCONF='kuma.core.tests.logging_urls')
class LoggingTests(KumaTestCase):
    logger = logging.getLogger('django')
    suspicous_path = '/en-US/suspicious/'

    def setUp(self):
        super(LoggingTests, self).setUp()
        self.old_handlers = self.logger.handlers[:]

    def tearDown(self):
        super(LoggingTests, self).tearDown()
        self.logger.handlers = self.old_handlers

    def test_no_mail_handler(self):
        self.logger.handlers = [logging.NullHandler()]
        response = self.client.get(self.suspicous_path)
        assert 400 == response.status_code
        assert 0 == len(mail.outbox)

    def test_mail_handler(self):
        self.logger.handlers = [AdminEmailHandler()]
        response = self.client.get(self.suspicous_path)
        assert 400 == response.status_code
        assert 1 == len(mail.outbox)

        assert 'admin@example.com' in mail.outbox[0].to
        assert self.suspicous_path in mail.outbox[0].body


class SoapboxViewsTest(KumaTestCase):

    def test_global_home(self):
        m = Message(message='Global', is_global=True, is_active=True, url='/')
        m.save()

        url = reverse('home')
        r = self.client.get(url, follow=True)
        assert 200 == r.status_code

        doc = pq(r.content)
        assert m.message == doc.find('div.global-notice').text()

    def test_subsection(self):
        m = Message(message='Search', is_global=False, is_active=True,
                    url='/search/')
        m.save()

        url = reverse('search')
        r = self.client.get(url, follow=True)
        assert 200 == r.status_code

        doc = pq(r.content)
        assert m.message == doc.find('div.global-notice').text()

        url = reverse('home')
        r = self.client.get(url, follow=True)
        assert 200 == r.status_code

        doc = pq(r.content)
        assert not doc.find('div.global-notice')

    def test_inactive(self):
        m = Message(message='Search', is_global=False, is_active=False,
                    url='/search/')
        m.save()

        url = reverse('search')
        r = self.client.get(url, follow=True)
        assert 200 == r.status_code

        doc = pq(r.content)
        assert not doc.find('div.global-notice')


class EventsRedirectTest(KumaTestCase):

    def test_redirect_to_mozilla_org(self):
        url = '/en-US/events'
        response = self.client.get(url)
        assert 302 == response.status_code
        assert 'https://mozilla.org/contribute/events' == response['Location']


@pytest.mark.parametrize(
    'http_method', ['get', 'put', 'delete', 'options', 'head'])
def test_setting_language_cookie_disallowed_methods(client, http_method):
    url = reverse('set-language-cookie')
    response = getattr(client, http_method)(url, {'language': 'bn'})
    assert response.status_code == 405
    assert_no_cache_header(response)


def test_setting_language_cookie_working(client):
    url = reverse('set-language-cookie')
    response = client.post(url, {'language': 'bn'})
    assert response.status_code == 204
    assert_no_cache_header(response)

    lang_cookie = response.client.cookies.get(settings.LANGUAGE_COOKIE_NAME)

    # Check language cookie is set
    assert lang_cookie
    assert lang_cookie.value == 'bn'
    # Check that the max-age from the cookie is the same as our settings
    assert lang_cookie['max-age'] == settings.LANGUAGE_COOKIE_AGE


def test_not_possible_to_set_non_locale_cookie(client):
    url = reverse('set-language-cookie')
    response = client.post(url, {'language': 'foo'})
    assert response.status_code == 204
    assert_no_cache_header(response)
    # No language cookie should be saved as `foo` is not a supported locale
    assert not response.client.cookies.get(settings.LANGUAGE_COOKIE_NAME)


@pytest.mark.parametrize('method', ['get', 'head'])
def test_sitemap(client, settings, sitemaps, db, method):
    settings.MEDIA_ROOT = sitemaps['tmpdir'].realpath()
    response = getattr(client, method)(reverse('sitemap'))
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response['Content-Type'] == 'application/xml'
    if method == 'get':
        assert ''.join(
            [chunk.decode('utf-8') for chunk in response.streaming_content]
        ) == sitemaps['index']


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_sitemap_405s(client, db, method):
    response = getattr(client, method)(reverse('sitemap'))
    assert response.status_code == 405
    assert_shared_cache_header(response)


@pytest.mark.parametrize('method', ['get', 'head'])
def test_sitemaps(client, settings, sitemaps, db, method):
    settings.MEDIA_ROOT = sitemaps['tmpdir'].realpath()
    response = getattr(client, method)(
        reverse(
            'sitemaps',
            kwargs={'path': 'sitemaps/en-US/sitemap.xml'}
        )
    )
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response['Content-Type'] == 'application/xml'
    if method == 'get':
        assert (''.join([chunk.decode('utf-8') for chunk in response.streaming_content]) ==
                sitemaps['locales']['en-US'])


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_sitemaps_405s(client, db, method):
    response = getattr(client, method)(
        reverse(
            'sitemaps',
            kwargs={'path': 'sitemaps/en-US/sitemap.xml'}
        )
    )
    assert response.status_code == 405
    assert_shared_cache_header(response)


def test_ratelimit_429(client, db):
    '''Custom 429 view is used for Ratelimited exception.'''
    url = reverse('home')
    with mock.patch('kuma.landing.views.render') as render:
        render.side_effect = Ratelimited()
        response = client.get(url)
    assert response.status_code == 429
    assert '429.html' in [t.name for t in response.templates]
    assert response['Retry-After'] == '60'
    assert_no_cache_header(response)


def test_error_handler_minimal_request(rf, db, settings):
    '''Error page renders if middleware hasn't added request members.'''
    # Setup conditions for adding analytics with a flag check
    settings.GOOGLE_ANALYTICS_ACCOUNT = 'UA-00000000-0'
    Flag.objects.create(name='section_edit', authenticated=True)

    # Create minimal request
    request = rf.get('/en-US/docs/tags/Open Protocol')
    assert not hasattr(request, 'LANGUAGE_CODE')
    assert not hasattr(request, 'user')

    # Generate the 500 page
    exception = Exception('Something went wrong.')
    response = handler500(request, exception)
    assert response.status_code == 500
    assert b'Internal Server Error' in response.content
