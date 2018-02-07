from mock import patch, MagicMock

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from kuma.core.tests import KumaTestCase, eq_
from kuma.core.middleware import (
    GZipMiddleware,
    WhiteNoiseMiddleware,
    SetRemoteAddrFromForwardedFor,
    ForceAnonymousSessionMiddleware,
    RestrictedEndpointsMiddleware,
    RestrictedWhiteNoiseMiddleware,
    LegacyDomainRedirectsMiddleware,
)


class TrailingSlashMiddlewareTestCase(KumaTestCase):
    def test_no_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez')
        eq_(response.status_code, 404)

    def test_404_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez/')
        eq_(response.status_code, 404)

    def test_remove_trailing_slash(self):
        response = self.client.get(u'/en-US/docs/files/?xxx=\xc3')
        eq_(response.status_code, 301)
        assert response['Location'].endswith('/en-US/docs/files?xxx=%C3%83')


class SetRemoteAddrFromForwardedForTestCase(KumaTestCase):

    def test_rate_x_forwarded_for(self):
        rf = RequestFactory()
        middleware = SetRemoteAddrFromForwardedFor()

        req1 = rf.get('/', HTTP_X_FORWARDED_FOR='1.1.1.1')
        middleware.process_request(req1)
        eq_(req1.META['REMOTE_ADDR'], '1.1.1.1')

        req2 = rf.get('/', HTTP_X_FORWARDED_FOR='2.2.2.2')
        middleware.process_request(req2)
        eq_(req2.META['REMOTE_ADDR'], '2.2.2.2')

        req3 = rf.get('/', HTTP_X_FORWARDED_FOR='3.3.3.3, 4.4.4.4')
        middleware.process_request(req3)
        eq_(req3.META['REMOTE_ADDR'], '3.3.3.3')


def test_force_anonymous_session_middleware(rf, settings):
    request = rf.get('/foo')
    request.COOKIES[settings.SESSION_COOKIE_NAME] = 'totallyfake'

    middleware = ForceAnonymousSessionMiddleware()
    middleware.process_request(request)

    assert request.session
    assert request.session.session_key is None

    response = middleware.process_response(request, MagicMock())

    assert not response.method_calls


def test_restricted_endpoints_middleware(rf, settings):
    settings.ATTACHMENT_HOST = 'demos'
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    middleware = RestrictedEndpointsMiddleware()

    request = rf.get('/foo', HTTP_HOST='demos')
    middleware.process_request(request)
    assert request.urlconf == 'kuma.urls_untrusted'

    request = rf.get('/foo', HTTP_HOST='not-demos')
    middleware.process_request(request)
    assert not hasattr(request, 'urlconf')

    settings.ENABLE_RESTRICTIONS_BY_HOST = False
    request = rf.get('/foo', HTTP_HOST='demos')
    middleware.process_request(request)
    assert not hasattr(request, 'urlconf')


def test_restricted_whitenoise_middleware(rf, settings):
    settings.ATTACHMENT_HOST = 'demos'
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    middleware = RestrictedWhiteNoiseMiddleware()

    sentinel = object()

    with patch.object(WhiteNoiseMiddleware, 'process_request',
                      return_value=sentinel):
        request = rf.get('/foo', HTTP_HOST='demos')
        assert middleware.process_request(request) is None

        request = rf.get('/foo', HTTP_HOST='not-demos')
        assert middleware.process_request(request) is sentinel

        settings.ENABLE_RESTRICTIONS_BY_HOST = False
        request = rf.get('/foo', HTTP_HOST='demos')
        assert middleware.process_request(request) is sentinel


@pytest.mark.parametrize('host', ['old1', 'old2', 'old3', 'new'])
@pytest.mark.parametrize('site_url', ['http://new', 'https://new'])
def test_legacy_domain_redirects_middleware(rf, settings, site_url, host):
    path = '/foo/bar?x=3&y=yes'
    settings.SITE_URL = site_url
    settings.LEGACY_HOSTS = ['old1', 'old2', 'old3']
    middleware = LegacyDomainRedirectsMiddleware()

    request = rf.get(path, HTTP_HOST=host)
    response = middleware.process_request(request)

    if host in settings.LEGACY_HOSTS:
        assert response.status_code == 301
        assert 'Location' in response
        assert response['Location'] == site_url + path
    else:
        assert response is None


@pytest.mark.parametrize(
    'etag_header',
    (None, '"7ac66c0f148de9519b8bd264312c4d64"')
)
def test_gzip_middleware(rf, etag_header):
    """
    Test that GZipMiddleware does not modify the ETag header unlike
    Django's GZipMiddleware.

    TODO: When moving to Django 1.11, this test code and the GZipMiddleware
          code in kuma.core.middleware can be deleted, and Django's
          GZipMiddleware should be used instead.
    """
    request = rf.get('/foo/bar', HTTP_ACCEPT_ENCODING='gzip')
    response = HttpResponse(50 * 'yada ')
    if etag_header:
        response['etag'] = etag_header

    response_out = GZipMiddleware().process_response(request, response)

    if etag_header:
        # The ETag header is still there and hasn't been modified.
        assert 'etag' in response_out
        assert response_out['etag'] == etag_header
    else:
        assert 'etag' not in response
