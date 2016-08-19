import pytest


@pytest.fixture(scope='session')
def base_url(base_url, request):
    return base_url or 'https://developer.allizom.org'

