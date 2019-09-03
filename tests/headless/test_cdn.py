from urllib import quote

import pytest
import requests


DEFAULT_TIMEOUT = 120  # seconds


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


def request(method, url, **kwargs):
    if 'timeout' not in kwargs:
        kwargs.update(timeout=DEFAULT_TIMEOUT)
    if 'allow_redirects' not in kwargs:
        kwargs.update(allow_redirects=False)
    return requests.request(method, url, **kwargs)


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


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug', ['/_kuma_status.json',
             '/en-US/search',
             '/en-US/profiles/sheppy',
             '/en-US/users/signin',
             '/en-US/users/account/signin/error',
             '/en-US/unsubscribe/1',
             '/admin/login/',
             '/media/revision.txt',
             '/media/kumascript-revision.txt'])
def test_not_cached(base_url, is_behind_cdn, slug):
    """Ensure that these endpoints that should return a 200 are not cached."""
    assert_not_cached(base_url + slug, 200, is_behind_cdn)


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug', ['/healthz',
             '/readiness'])
def test_not_cached_204(base_url, is_behind_cdn, slug):
    """Ensure that these endpoints that should return a 204 are not cached."""
    assert_not_cached(base_url + slug, 204, is_behind_cdn)


@pytest.mark.nondestructive
def test_maintenance_mode(base_url, is_behind_cdn, is_maintenance_mode):
    """Ensure that the maintenance-mode page/redirect is not cached."""
    url = base_url + '/en-US/maintenance-mode'
    assert_not_cached(url, 200 if is_maintenance_mode else 302, is_behind_cdn)


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug', ['/en-US/dashboards/spam',
             '/en-US/dashboards/revisions',
             '/en-US/profile',
             '/en-US/docs/new?slug=test',
             '/en-US/docs/preview-wiki-content',
             '/en-US/docs/Web/HTML$edit',
             '/en-US/docs/Web/HTML$move',
             '/en-US/docs/Web/HTML$files',
             '/en-US/docs/Web/HTML$purge',
             '/en-US/docs/Web/HTML$delete',
             '/en-US/docs/Web/HTML$translate',
             '/en-US/docs/Web/HTML$quick-review',
             '/en-US/docs/Web/HTML$revert/1293895',
             '/en-US/docs/Web/HTML$repair_breadcrumbs'])
def test_not_cached_login_required(base_url, is_behind_cdn, slug):
    """Ensure that these endpoints that require login are not cached."""
    url = base_url + slug
    response = assert_not_cached(url, 302, is_behind_cdn)
    assert response.headers['location'].endswith(
        '/users/signin?next=' + quote(slug))


@pytest.mark.nondestructive
@pytest.mark.parametrize('slug', ['/admin/users/user/1/'])
def test_not_cached_admin_login_required(base_url, is_behind_cdn, slug):
    """Ensure that these endpoints that require admin login are not cached."""
    url = base_url + slug
    response = assert_not_cached(url, 302, is_behind_cdn)
    assert response.headers['location'].endswith(
        '/admin/login/?next=' + quote(slug))


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug', ['/en-US/docs/submit_akismet_spam',
             '/en-US/docs/Web/HTML$subscribe',
             '/en-US/docs/Web/HTML$subscribe_to_tree'])
def test_not_cached_post_requires_login(base_url, is_behind_cdn, slug):
    """
    Ensure that POST's to these endpoints that require login are not cached.
    """
    url = base_url + slug
    response = assert_not_cached(url, 302, is_behind_cdn, method='post')
    assert response.headers['location'].endswith(
        '/users/signin?next=' + quote(slug))


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug',
    ['/en-US/',
     '/en-US/promote',
     '/en-US/promote/buttons',
     '/en-US/dashboards/macros',
     '/robots.txt',
     '/contribute.json',
     '/humans.txt',
     '/sitemap.xml',
     '/sitemaps/en-US/sitemap.xml',
     '/diagrams/workflow/workflow.svg',
     '/presentations/microsummaries/index.html',
     '/en-US/search/xml',
     '/en-US/docs.json?slug=Web/HTML',
     '/en-US/docs/Web/HTML$json',
     '/en-US/docs/Web/HTML$history',
     '/en-US/docs/Web/HTML$children',
     '/en-US/docs/Web/HTML$revision/1293895',
     '/en-US/docs/Web/HTML$compare?locale=en-US&to=1299417&from=1293895',
     '/en-US/docs/Learn/CSS#Modules',
     '/en-US/docs/Learn/CSS$toc',
     '/fr/docs/feeds/rss/l10n-updates',
     '/fr/docs/localization-tag/inprogress',
     '/en-US/docs/all',
     '/en-US/docs/ckeditor_config.js',
     '/en-US/docs/feeds/atom/files',
     '/en-US/docs/feeds/rss/all',
     '/en-US/docs/feeds/rss/needs-review',
     '/en-US/docs/feeds/rss/needs-review/technical',
     '/en-US/docs/feeds/rss/revisions',
     '/en-US/docs/feeds/rss/tag/CSS',
     '/en-US/docs/needs-review/editorial',
     '/en-US/docs/tag/ARIA',
     '/en-US/docs/tags',
     '/en-US/docs/top-level',
     '/en-US/docs/with-errors',
     '/en-US/docs/without-parent'])
def test_cached(base_url, is_behind_cdn, is_local_url, is_searchable, slug):
    """Ensure that these requests that should return 200 are cached."""
    if is_local_url:
        if any(slug.startswith(p) for p in ('/diagrams/', '/presentations/')):
            pytest.xfail('legacy files are typically not served from a '
                         'local development instance')
        elif (not is_searchable) and slug.endswith('/dashboards/macros'):
            pytest.xfail('search is not available and populated')
    assert_cached(base_url + slug, 200, is_behind_cdn)


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug', ['/files/2767/hut.jpg',
             '/@api/deki/files/3613/=hut.jpg',
             '/en-US/dashboards/localization'])
def test_cached_301(base_url, is_behind_cdn, is_local_url, slug):
    """Ensure that these requests that should return 301 are cached."""
    if is_local_url and any(slug.startswith(p) for p in ('/files/', '/@api/')):
        pytest.xfail('attachments are typically not served from a '
                     'local development instance')
    assert_cached(base_url + slug, 301, is_behind_cdn)


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug', ['/favicon.ico',
             '/en-US/events',
             '/en-US/Firefox',
             '/en-US/Firefox$json',
             '/en-US/Firefox$history',
             '/en-US/Firefox$children'])
def test_cached_302(base_url, is_behind_cdn, slug):
    """Ensure that these requests that should return 302 are cached."""
    assert_cached(base_url + slug, 302, is_behind_cdn)


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'zone', ['Add-ons', 'Apps', 'Firefox', 'Learn', 'Marketplace'])
@pytest.mark.parametrize(
    'slug', ['/{}',
             '/{}$json',
             '/{}$history',
             '/{}$children'])
def test_no_locale_cached_302(base_url, is_behind_cdn, slug, zone):
    """
    Ensure that these zone requests without a locale that should return
    302 are cached.
    """
    response = assert_cached(base_url + slug.format(zone), 302, is_behind_cdn)
    assert response.headers['location'].startswith('/docs/')


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug, params',
    [('/en-US/dashboards/topic_lookup', {'topic': 'mathml'}),
     ('/en-US/dashboards/user_lookup', {'user': 'sheppy'})],
    ids=['topic_lookup', 'user_lookup'])
def test_lookup_dashboards(base_url, is_behind_cdn, slug, params):
    """
    Ensure that the topic and user dashboards require login.
    """
    response = assert_cached(base_url + slug, 302, is_behind_cdn)
    assert response.headers['location'].endswith(
        '/users/signin?next=' + quote(slug))


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    'slug', ['/en-US/docs/Web/HTML'])
def test_documents_with_cookie_and_param(base_url, is_behind_cdn, is_local_url,
                                         slug):
    """
    Ensure that the "dwf_sg_task_completion" cookie, and query
    parameters are forwarded/cached-on for document requests.
    """
    url = base_url + slug
    response1 = assert_cached(url, 200, is_behind_cdn,
                              cookies={'dwf_sg_task_completion': 'True'})
    response2 = assert_cached(url, 200, is_behind_cdn,
                              cookies={'dwf_sg_task_completion': 'False'})
    response3 = assert_cached(url + '?raw=true', 200, is_behind_cdn)
    assert response3.content != response2.content
    assert response3.content != response1.content
    if is_local_url:
        pytest.xfail('the sg_task_completion waffle flag is not '
                     'enabled by default in the sample database')
    assert response2.content != response1.content


# Test value tuple is:
# - Expected locale prefix
# - Accept-Language header value
# - django-language cookie settings (False to omit)
# - ?lang param value (False to omit)
LOCALE_SELECTORS = {
    'en-US': ('en-US', 'en-US', False, False),
    'es': ('es', 'es', False, False),
    'fr-cookie': ('fr', 'es', 'fr', False),
    'de-param': ('de', 'es', 'fr', 'de'),
}


@pytest.mark.nondestructive
@pytest.mark.parametrize('expected,accept,cookie,param',
                         LOCALE_SELECTORS.values(),
                         ids=LOCALE_SELECTORS.keys())
@pytest.mark.parametrize(
    'slug',
    ['/search',
     '/events',
     '/profile',
     '/promote',
     '/profiles/sheppy',
     '/unsubscribe/1',
     '/docs.json?slug=Web/HTML',
     '/docs/Web/HTML',
     '/docs/Web/HTML$json',
     '/docs/Web/HTML$history',
     '/docs/Web/HTML$children',
     '/docs/Web/HTML$revision/1293895',
     '/docs/Web/HTML$repair_breadcrumbs',
     '/docs/Web/HTML$compare?locale=en-US&to=1299417&from=1293895',
     '/docs/Learn/CSS/Styling_text/Fundamentals#Color',
     '/docs/Learn/CSS/Styling_text/Fundamentals$toc',
     '/docs/feeds/rss/l10n-updates',
     '/docs/localization-tag/inprogress',
     '/docs/all',
     '/docs/new?slug=test',
     '/docs/preview-wiki-content',
     '/docs/ckeditor_config.js',
     '/docs/feeds/atom/files',
     '/docs/feeds/rss/all',
     '/docs/feeds/rss/needs-review',
     '/docs/feeds/rss/needs-review/technical',
     '/docs/feeds/rss/revisions',
     '/docs/feeds/rss/tag/CSS',
     '/docs/needs-review/editorial',
     '/docs/tag/ARIA',
     '/docs/tags',
     '/docs/top-level',
     '/docs/with-errors',
     '/docs/without-parent',
     '/dashboards/spam',
     '/dashboards/macros',
     '/dashboards/revisions',
     '/dashboards/localization',
     '/dashboards/topic_lookup',
     '/dashboards/user_lookup'])
def test_locale_selection_cached(base_url, is_behind_cdn, is_local_url, slug,
                                 expected, accept, cookie, param):
    """
    Ensure that locale selection, which depends on the "lang" query
    parameter, the "django_language" cookie, and the "Accept-Language"
    header, works and is cached for the provided URL's. It's not necessary
    that these redirections are cached, but they are because they fall into
    behaviors that do.
    """
    url = base_url + slug
    assert expected, "expected must be set to the expected locale prefix."
    assert accept, "accept must be set to the Accept-Language header value."

    request_kwargs = {
        'headers': {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept-Language': accept
        }
    }
    if cookie:
        request_kwargs['cookies'] = {'django_language': cookie}
    if param:
        request_kwargs['params'] = {'lang': param}

    response = assert_cached(url, 302, is_behind_cdn, **request_kwargs)
    expected = '/' + expected + '/'
    assert response.headers['location'].startswith(expected)


@pytest.mark.nondestructive
@pytest.mark.parametrize('expected,accept,cookie,param',
                         LOCALE_SELECTORS.values(),
                         ids=LOCALE_SELECTORS.keys())
@pytest.mark.parametrize(
    'slug', ['/users/signin',
             '/docs/Web/HTML$edit',
             '/docs/Web/HTML$move',
             '/docs/Web/HTML$files',
             '/docs/Web/HTML$purge',
             '/docs/Web/HTML$delete',
             '/docs/Web/HTML$translate',
             '/docs/Web/HTML$quick-review',
             '/docs/Web/HTML$subscribe',
             '/docs/Web/HTML$subscribe_to_tree',
             '/docs/Web/HTML$revert/1293895'])
def test_locale_selection_not_cached(base_url, is_behind_cdn, is_local_url,
                                     slug, expected, accept, cookie, param):
    """
    Ensure that locale selection, which depends on the "lang" query
    parameter, the "django_language" cookie, and the "Accept-Language"
    header, works and is not cached for the provided URL's. It's not
    necessary that these redirections are not cached, but they are not
    because they fall into behaviors that do not.
    """
    url = base_url + slug
    assert expected, "expected must be set to the expected locale prefix."
    assert accept, "accept must be set to the Accept-Langauge header value."

    request_kwargs = {
        'headers': {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept-Language': accept
        }
    }

    if cookie:
        request_kwargs['cookies'] = {'django_language': cookie}
    if param:
        request_kwargs['params'] = {'lang': param}

    if is_behind_cdn:
        response = assert_not_cached(url, 302, **request_kwargs)
    else:
        response = request('get', url, **request_kwargs)
        assert response.status_code == 302
    expected = '/' + expected + '/'
    assert response.headers['location'].startswith(expected)


@pytest.mark.nondestructive
@pytest.mark.parametrize('locale', [None, '/de'])
@pytest.mark.parametrize(
    'zone', ['Add-ons', 'Apps', 'Firefox', 'Learn', 'Marketplace'])
@pytest.mark.parametrize(
    'slug', ['{}/{}$edit',
             '{}/{}$move',
             '{}/{}$files',
             '{}/{}$purge',
             '{}/{}$delete',
             '{}/{}$translate',
             '{}/{}$quick-review',
             '{}/{}$revert/1284393'])
def test_former_vanity_302(base_url, is_behind_cdn, slug, zone, locale):
    """
    Ensure that these former zone vanity URL's that should return 302 are
    cached (based on Cache-Control header) when not behind a CDN, and not
    cached (based on a special CDN header) when behind a CDN. They are not
    cached when behind a CDN simply because they fall into into a CDN behavior
    that prevents caching, not because they shouldn't be cached.
    """
    locale = locale or ''
    url = base_url + slug.format(locale, zone)
    assert_caching = assert_not_cached if is_behind_cdn else assert_cached
    response = assert_caching(url, 302, is_behind_cdn)
    assert response.headers['location'].startswith('{}/docs/'.format(locale))
    assert response.headers['location'].endswith(slug.format('', zone))


@pytest.mark.nondestructive
@pytest.mark.parametrize('locale', [None, '/de'])
@pytest.mark.parametrize(
    'zone', ['Add-ons', 'Apps', 'Firefox', 'Learn', 'Marketplace'])
@pytest.mark.parametrize(
    'slug', ['{}/{}$subscribe',
             '{}/{}$subscribe_to_tree'])
def test_former_vanity_302_post(base_url, is_behind_cdn, slug, zone, locale):
    """
    Ensure that POST's to these former zone vanity URL's that should return
    302 are cached (based on Cache-Control header) when not behind a CDN, and
    not cached (based on a special CDN header) when behind a CDN. They are not
    cached when behind a CDN simply because they fall into a CDN behavior that
    prevents caching, not because they shouldn't be cached.
    """
    url = base_url + slug.format(locale or '', zone)
    assert_caching = assert_not_cached if is_behind_cdn else assert_cached
    assert_caching(url, 302, is_behind_cdn, method='post')
