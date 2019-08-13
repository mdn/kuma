import pytest

from . import request


def is_cloudfront_cache_hit(response):
    """CloudFront specific check for evidence of a cache hit."""
    return (response.headers['x-cache'] in ('Hit from cloudfront',
                                            'RefreshHit from cloudfront'))


def is_cloudfront_cache_miss(response):
    """CloudFront specific check for evidence of a cache miss."""
    return response.headers['x-cache'] == 'Miss from cloudfront'


def is_cloudfront_error(response):
    """CloudFront specific check for evidence of an error response."""
    return response.headers['x-cache'] == 'Error from cloudfront'


def is_cdn_cache_hit(response):
    """Checks the response for evidence of a cache hit on the CDN."""
    return is_cloudfront_cache_hit(response)


def is_cdn_cache_miss(response):
    """Checks the response for evidence of a cache miss on the CDN."""
    return is_cloudfront_cache_miss(response)


def is_cdn_error(response):
    """Checks the response for evidence of an error from the CDN."""
    return is_cloudfront_error(response)


def assert_not_cached_by_cdn(url, expected_status_code=200, method='get',
                             **request_kwargs):
    response = request(method, url, **request_kwargs)
    assert response.status_code == expected_status_code
    if expected_status_code >= 400:
        assert is_cdn_error(response)
    else:
        assert is_cdn_cache_miss(response)
    return response


def assert_not_cached(url, expected_status_code=200, is_behind_cdn=True,
                      method='get', **request_kwargs):
    if is_behind_cdn:
        response1 = assert_not_cached_by_cdn(url, expected_status_code, method,
                                             **request_kwargs)
        response2 = assert_not_cached_by_cdn(url, expected_status_code, method,
                                             **request_kwargs)
        if expected_status_code in (301, 302):
            assert (response2.headers['location'] ==
                    response1.headers['location'])
        return response2

    response = request(method, url, **request_kwargs)
    assert response.status_code == expected_status_code
    assert 'no-cache' in response.headers['Cache-Control']
    assert 'no-store' in response.headers['Cache-Control']
    assert 'must-revalidate' in response.headers['Cache-Control']
    assert 'max-age=0' in response.headers['Cache-Control']
    return response


def assert_cached(url, expected_status_code=200, is_behind_cdn=True,
                  method='get', **request_kwargs):
    response = request(method, url, **request_kwargs)
    assert response.status_code == expected_status_code
    if is_behind_cdn:
        if is_cdn_cache_miss(response):
            response2 = request(method, url, **request_kwargs)
            assert response2.status_code == expected_status_code
            assert is_cdn_cache_hit(response2)
            if expected_status_code == 200:
                assert response2.content == response.content
            elif expected_status_code in (301, 302):
                assert (response2.headers['location'] ==
                        response.headers['location'])
        else:
            assert is_cdn_cache_hit(response)
    else:
        assert 'public' in response.headers['Cache-Control']
        assert (('max-age' in response.headers['Cache-Control']) or
                ('s-maxage' in response.headers['Cache-Control']))
    return response


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug,status', [('/_kuma_status.json', 200),
                    ('/healthz', 204),
                    ('/readiness', 204),
                    ('/api/v1/whoami', 200),
                    ('/api/v1/doc/en-US/Web/CSS', 200),
                    ('/api/v1/search/en-US?q=css', 200),
                    ('/en-US/search?q=css', 200),
                    ('/en-US/profile', 302),
                    ('/en-US/profile/edit', 302),
                    ('/en-US/profiles/sheppy', 200),
                    ('/en-US/profiles/sheppy/edit', 403),
                    ('/en-US/profiles/sheppy/delete', 403),
                    ('/en-US/users/signin', 200),
                    ('/en-US/users/signup', 200),
                    ('/en-US/users/signout', 302),
                    ('/en-US/users/account/inactive', 200),
                    ('/en-US/users/account/signup', 302),
                    ('/en-US/users/account/signin/error', 200),
                    ('/en-US/users/account/signin/cancelled', 200),
                    ('/en-US/users/account/email', 302),
                    ('/en-US/users/account/email/confirm', 200),
                    ('/en-US/users/account/email/confirm/1', 200),
                    ('/en-US/users/account/recover/sent', 200),
                    ('/en-US/users/account/recover/done', 302),
                    ('/admin/login/', 200),
                    ('/admin/users/user/1/', 302),
                    ('/admin/wiki/document/purge/', 302),
                    ('/media/revision.txt', 200),
                    ('/media/kumascript-revision.txt', 200)])
def test_not_cached(site_url, is_behind_cdn, slug, status):
    """Ensure that these endpoints respond as expected and are not cached."""
    assert_not_cached(site_url + slug, status, is_behind_cdn)


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug,status', [('/miel', 500),
                    ('/en-US/', 200),
                    ('/en-US/events', 302),
                    ('/robots.txt', 200),
                    ('/favicon.ico', 302),
                    ('/contribute.json', 200),
                    ('/humans.txt', 200),
                    ('/sitemap.xml', 200),
                    ('/sitemaps/en-US/sitemap.xml', 200),
                    ('/files/2767/hut.jpg', 301),
                    ('/@api/deki/files/3613/=hut.jpg', 301),
                    ('/diagrams/workflow/workflow.svg', 200),
                    ('/presentations/microsummaries/index.html', 200),
                    ('/en-US/search/xml', 200),
                    ('/en-US/docs.json?slug=Web/HTML', 200),
                    ('/en-US/Firefox', 302),
                    ('/en-US/docs/Web/HTML', 200),
                    ('/en-US/docs/Web/HTML$json', 200),
                    ('/en-US/docs/Web/HTML$children', 200)])
def test_cached(site_url, is_behind_cdn, is_local_url, slug, status):
    """Ensure that these requests are cached."""
    if is_local_url:
        if any(slug.startswith(p) for p in
               ('/diagrams/', '/presentations/', '/files/', '/@api/')):
            pytest.xfail('attachments and legacy files are typically not '
                         'served from a local development instance')
    assert_cached(site_url + slug, status, is_behind_cdn)


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'zone', ['Add-ons', 'Apps', 'Firefox', 'Learn', 'Marketplace'])
@pytest.mark.parametrize(
    'slug', ['/{}',
             '/{}$json',
             '/{}$children'])
def test_no_locale_cached_302(site_url, is_behind_cdn, slug, zone):
    """
    Ensure that these zone requests without a locale that should return
    302 are cached.
    """
    response = assert_cached(site_url + slug.format(zone), 302, is_behind_cdn)
    assert response.headers['location'].startswith('/docs/')


@pytest.mark.headless
@pytest.mark.nondestructive
def test_document_with_cookie_and_param(site_url, is_behind_cdn, is_local_url):
    """
    Ensure that the "dwf_sg_task_completion" cookie, and query
    parameters are forwarded/cached-on for document requests.
    """
    url = site_url + '/en-US/docs/Web/HTML'
    response1 = assert_cached(url, 200, is_behind_cdn,
                              cookies={'dwf_sg_task_completion': 'True'})
    response2 = assert_cached(url, 200, is_behind_cdn,
                              cookies={'dwf_sg_task_completion': 'False'})
    response3 = assert_cached(url + '?redirect=no', 200, is_behind_cdn)
    assert response3.content != response2.content
    assert response3.content != response1.content
    if is_local_url:
        pytest.xfail('the sg_task_completion waffle flag is not '
                     'enabled by default in the sample database')
    assert response2.content != response1.content
