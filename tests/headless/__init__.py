import pytest

# Use pytest verbose asserts
# https://stackoverflow.com/questions/41522767/pytest-assert-introspection-in-helper-function
pytest.register_assert_rewrite('utils.urls')


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
