from __future__ import absolute_import

import pytest

from utils.urls import assert_valid_url
from .map_301 import (REDIRECT_URLS, GITHUB_IO_URLS, MOZILLADEMOS_URLS,
                      LEGACY_URLS)

# while these test methods are similar, they're each testing a
# subset of redirects, and it was easier to work with them separately.


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', REDIRECT_URLS)
def test_redirects(url, base_url):
    url['base_url'] = base_url
    assert_valid_url(**url)


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', GITHUB_IO_URLS)
def test_github_redirects(url, base_url):
    url['base_url'] = base_url
    assert_valid_url(**url)


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', MOZILLADEMOS_URLS)
def test_mozillademos_redirects(url, base_url):
    url['base_url'] = base_url
    assert_valid_url(**url)


@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', LEGACY_URLS)
def test_legacy_urls(url, base_url):
    url['base_url'] = base_url
    assert_valid_url(**url)
