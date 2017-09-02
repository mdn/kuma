import pytest

from kuma.core.urlresolvers import reverse


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


@pytest.mark.parametrize('method', ['get', 'head'])
def test_sitemap(client, settings, sitemaps, db, method):
    settings.MEDIA_ROOT = sitemaps['tmpdir'].realpath()
    response = getattr(client, method)(reverse('sitemap'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/xml'
    if method == 'get':
        assert ''.join(response.streaming_content) == sitemaps['index']


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_sitemap_405s(client, db, method):
    response = getattr(client, method)(reverse('sitemap'))
    assert response.status_code == 405


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
    assert response['Content-Type'] == 'application/xml'
    if method == 'get':
        assert (''.join(response.streaming_content) ==
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
