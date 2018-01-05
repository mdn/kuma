from datetime import datetime

import pytest
from django.conf import settings
from django.core.cache import caches

from kuma.wiki.models import Document, Revision


@pytest.fixture()
def cleared_cacheback_cache():
    caches[settings.CACHEBACK_CACHE_ALIAS].clear()
    yield
    caches[settings.CACHEBACK_CACHE_ALIAS].clear()


@pytest.fixture
def wiki_user(db, django_user_model):
    """A test user."""
    return django_user_model.objects.create(
        username='wiki_user',
        email='wiki_user@example.com',
        date_joined=datetime(2017, 4, 14, 12, 0))


@pytest.fixture
def root_doc(wiki_user):
    """A newly-created top-level English document."""
    root_doc = Document.objects.create(
        locale='en-US', slug='Root', title='Root Document')
    Revision.objects.create(
        document=root_doc,
        creator=wiki_user,
        content='<p>Getting started...</p>',
        title='Root Document',
        created=datetime(2017, 4, 14, 12, 15))
    return root_doc
