import pytest
import requests


# Use pytest verbose asserts
# https://stackoverflow.com/questions/41522767/pytest-assert-introspection-in-helper-function
pytest.register_assert_rewrite('utils.urls')


DEFAULT_TIMEOUT = 120  # seconds

# Untrusted attachments and samples domains that are indexed
INDEXED_ATTACHMENT_DOMAINS = set((
    'mdn.mozillademos.org',          # Main attachments domain
    'demos.mdn.mozit.cloud',         # Alternate attachments domain (testing)
    'demos-origin.mdn.mozit.cloud',  # Attachments origin
))

# Kuma web domains that are indexed
INDEXED_WEB_DOMAINS = set((
    'developer.mozilla.org',    # Main website, CDN origin
))


def request(method, url, **kwargs):
    if 'timeout' not in kwargs:
        kwargs.update(timeout=DEFAULT_TIMEOUT)
    if 'allow_redirects' not in kwargs:
        kwargs.update(allow_redirects=False)
    return requests.request(method, url, **kwargs)
