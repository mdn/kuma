from urlparse import urljoin, urlsplit

import pytest
import requests


@pytest.mark.smoke
@pytest.mark.nodata
@pytest.mark.nondestructive
def test_robots(base_url):
    urlbits = urlsplit(base_url)
    url = urljoin(base_url, 'robots.txt')
    response = requests.get(url)
    assert response.status_code == 200
    if urlbits.hostname == 'developer.mozila.org':
        assert 'Sitemap: ' in response.content
    else:
        assert 'Disallow: /' in response.content
