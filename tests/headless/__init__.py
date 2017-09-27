import pytest

# Use pytest verbose asserts
# https://stackoverflow.com/questions/41522767/pytest-assert-introspection-in-helper-function
pytest.register_assert_rewrite('utils.urls')
