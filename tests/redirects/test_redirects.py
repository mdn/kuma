from __future__ import absolute_import
from operator import itemgetter

import pytest

from .base import assert_valid_url
from .map_301 import URLS as REDIRECT_URLS

@pytest.mark.headless
@pytest.mark.nondestructive
@pytest.mark.parametrize('url', REDIRECT_URLS)
def test_redirects(url):
    url['base_url'] = "https://developer.mozilla.org"
    assert_valid_url(**url)
