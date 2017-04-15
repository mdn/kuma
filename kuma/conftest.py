import pytest
from django.conf import settings
from django.core.cache import caches
from django.utils.translation import trans_real

from kuma.core.tests import SessionAwareClient, LocalizingClient


@pytest.fixture
def db_and_empty_caches(db):
    """
    Use this fixture to emulate KumaTestCase. In addition to the
    standard set-up and tear-down that the "db" fixture provides
    (to emulate django.test.TestCase), it will clear the caches
    before (but not after) the test is run.
    """
    for cache in caches.all():
        cache.clear()

    trans_real.deactivate()
    trans_real._translations.clear()  # Django fails to clear this cache.
    trans_real.activate(settings.LANGUAGE_CODE)


@pytest.fixture
def session_aware_client():
    """
    Provides a session-aware client.
    """
    return SessionAwareClient()


@pytest.fixture
def localizing_client():
    """
    Provides a session-aware client that localizes requests without a locale
    in their requested URL.
    """
    return LocalizingClient()
