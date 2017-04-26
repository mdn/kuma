import pytest
from django.conf import settings
from django.core.cache import caches


@pytest.fixture()
def cleared_cacheback_cache():
    caches[settings.CACHEBACK_CACHE_ALIAS].clear()
