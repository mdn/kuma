import pytest
from django.test import RequestFactory
from mock import MagicMock, patch

from ..middleware import (
    ForceAnonymousSessionMiddleware,
    LegacyDomainRedirectsMiddleware,
    RestrictedEndpointsMiddleware,
    RestrictedWhiteNoiseMiddleware,
    SetRemoteAddrFromForwardedFor,
    WhiteNoiseMiddleware,
)


@pytest.mark.xfail(reason='is_valid_path always returns True')
@pytest.mark.parametrize('path', ('/missing_url', '/missing_url/'))
def test_remove_slash_middleware_keep_404(client, db, path):
    '''The RemoveSlashMiddleware retains 404s.'''
    response = client.get(path)
    assert response.status_code == 404


@pytest.mark.xfail(reason='is_valid_path always returns True')
def test_remove_slash_middleware_fixes_url(client, db):
    '''The RemoveSlashMiddleware fixes a URL that shouldn't have a slash.'''
    response = client.get(u'/contribute.json/')
    assert response.status_code == 301
    assert response['Location'].endswith('/contribute.json')


@pytest.mark.xfail(reason='is_valid_path always returns True')
def test_remove_slash_middleware_retains_querystring(client, db):
    '''The RemoveSlashMiddleware handles encoded querystrings.'''
    response = client.get(u'/contribute.json/?xxx=\xc3')
    assert response.status_code == 301
    assert response['Location'].endswith('/contribute.json?xxx=%C3%83')


@pytest.mark.parametrize(
    'forwarded_for,remote_addr',
    (('1.1.1.1', '1.1.1.1'),
     ('2.2.2.2', '2.2.2.2'),
     ('3.3.3.3, 4.4.4.4', '3.3.3.3')))
def test_set_remote_addr_from_forwarded_for(rf, forwarded_for, remote_addr):
    '''SetRemoteAddrFromForwardedFor parses the X-Forwarded-For Header.'''
    rf = RequestFactory()
    middleware = SetRemoteAddrFromForwardedFor()
    request = rf.get('/', HTTP_X_FORWARDED_FOR=forwarded_for)
    middleware.process_request(request)
    assert request.META['REMOTE_ADDR'] == remote_addr


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
