import pytest

# Use pytest verbose asserts
# https://stackoverflow.com/questions/41522767/pytest-assert-introspection-in-helper-function
pytest.register_assert_rewrite('utils.urls')


# Kuma web domains that are indexed
INDEXED_WEB_DOMAINS = set((
    'developer.mozilla.org',    # Main website, CDN origin
    'cdn.mdn.mozilla.net',      # Assets CDN
))
