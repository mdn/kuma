from urlparse import urlsplit

import pytest
import requests

from . import INDEXED_ATTACHMENT_DOMAINS, INDEXED_WEB_DOMAINS


@pytest.mark.smoke
@pytest.mark.headless
@pytest.mark.nondestructive
def test_robots(any_host_url):
    url = any_host_url + '/robots.txt'
    response = requests.get(url)
    assert response.status_code == 200

    urlbits = urlsplit(any_host_url)
    hostname = urlbits.netloc
    if hostname in INDEXED_ATTACHMENT_DOMAINS:
        assert response.content.strip() == ''
    elif hostname in INDEXED_WEB_DOMAINS:
        assert 'Sitemap: ' in response.content
        assert 'Disallow: /admin/\n' in response.content
    else:
        assert 'Disallow: /\n' in response.content
