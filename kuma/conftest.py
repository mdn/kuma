from datetime import datetime
from collections import namedtuple

import pytest
from django.conf import settings
from django.core.cache import caches

from kuma.wiki.models import Document, Revision


BannedUser = namedtuple('BannedUser', 'user ban')


@pytest.fixture()
def cleared_cacheback_cache():
    caches[settings.CACHEBACK_CACHE_ALIAS].clear()


@pytest.fixture
def wiki_user(db, django_user_model):
    """A test user."""
    return django_user_model.objects.create(
        username='wiki_user',
        email='wiki_user@example.com',
        date_joined=datetime(2017, 4, 14, 12, 0))


@pytest.fixture
def wiki_user_2(db, django_user_model):
    """A second test user."""
    return django_user_model.objects.create(
        username='wiki_user_2',
        email='wiki_user_2@example.com',
        date_joined=datetime(2017, 4, 17, 10, 30))


@pytest.fixture
def wiki_user_3(db, django_user_model):
    """A third test user."""
    return django_user_model.objects.create(
        username='wiki_user_3',
        email='wiki_user_3@example.com',
        date_joined=datetime(2017, 4, 23, 11, 45))


@pytest.fixture
def inactive_wiki_user(db, django_user_model):
    """An inactive test user."""
    return django_user_model.objects.create(
        is_active=False,
        username='wiki_user_slacker',
        email='wiki_user_slacker@example.com',
        date_joined=datetime(2017, 4, 19, 10, 58))


@pytest.fixture
def banned_wiki_user(db, django_user_model, wiki_user):
    """A banned test user."""
    user = django_user_model.objects.create(
        username='bad_wiki_user',
        email='bad_wiki_user@example.com',
        date_joined=datetime(2017, 4, 18, 9, 15)
    )
    ban = user.bans.create(by=wiki_user, reason='because')
    return BannedUser(user=user, ban=ban)


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


@pytest.fixture
def create_revision(root_doc):
    """A revision that created an English document."""
    return root_doc.revisions.first()
