import pytest
from django.test import RequestFactory
from mock import MagicMock, patch

from . import eq_, KumaTestCase
from ..middleware import (
    ForceAnonymousSessionMiddleware,
    LegacyDomainRedirectsMiddleware,
    RestrictedEndpointsMiddleware,
    RestrictedWhiteNoiseMiddleware,
    SessionMiddleware,
    SetRemoteAddrFromForwardedFor,
    SmartSessionMiddleware,
    WhiteNoiseMiddleware,
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
    'session_case',
    ['none', 'empty', 'anonymous-csrf', 'login-step', 'authenticated'])
def test_smart_session_middleware(rf, session_case):
    middleware = SmartSessionMiddleware()

    if session_case == 'authenticated':
        session = middleware.SessionStore('r35pvz8qwu0e0f5qtvbxi7rk6x763ty4')
        session.clear()
        session.update({
            '_auth_user_id': '922',
            'sociallogin_provider': 'github',
            'sociallogin_next_url': '/en-US/',
            '_auth_user_backend': 'kuma.users.auth_backends.KumaAuthBackend',
            '_auth_user_hash': 'e4b7a284fc0c109a5d73d85fb2a0e8b2fc22bfb3',
            '_csrftoken': ('ss5vqahzP0Ce33sZNfIOPa36npqLET3N'
                           'CvPySGs762lu20GspCp94yxpghgUdJED'),
        })
    elif session_case == 'login-step':
        session = middleware.SessionStore()
        session.update({
            'sociallogin_next_url': '/en-US/',
            'socialaccount_state': (
                {
                    'process': 'login',
                    'scope': '',
                    'auth_params': '',
                    'next': '/en-US/'
                },
                'mVUH9aPKwNHi'
            ),
        })
    elif session_case == 'anonymous-csrf':
        session = middleware.SessionStore()
        session['_csrftoken'] = ('ss5vqahzP0Ce33sZNfIOPa36npqLET3N'
                                 'CvPySGs762lu20GspCp94yxpghgUdJED'),
    elif session_case == 'empty':
        session = middleware.SessionStore()
    else:
        session = None

    response = object()

    request = rf.get('/foo')

    if session:
        request.session = session
        # Mimic the CsrfViewMiddleware.process_request call, which
        # causes the session's "accessed" attribute to be set.
        request.session.get('_csrftoken')

    with patch.object(SessionMiddleware, 'process_response') as base:
        middleware.process_response(request, response)
        assert base.called
        if session:
            replaced = (session_case in ('empty', 'anonymous-csrf'))
            assert request.session.accessed != replaced
            assert request.session.is_empty() == replaced
