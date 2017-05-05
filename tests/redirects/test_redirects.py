from __future__ import absolute_import

import pytest

from utils.urls import assert_valid_url
from .map_301 import URLS as REDIRECT_URLS
from .map_301 import GITHUB_IO_URLS
from .map_301 import MOZILLADEMOS_URLS

# while these test methods are similar, they're each testing a
# subset of redirects, and it was easier to work with them separately.
@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', REDIRECT_URLS)
def test_redirects(url):
    url['base_url'] = "https://developer.mozilla.org"
    assert_valid_url(**url)


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', GITHUB_IO_URLS)
def test_github_redirects(url):
    url['base_url'] = "https://developer.mozilla.org"
    assert_valid_url(**url)


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', MOZILLADEMOS_URLS)
def test_mozillademos_redirects(url):
    url['base_url'] = "https://developer.mozilla.org"
    assert_valid_url(**url)
