from datetime import datetime

import pytest
import requests_mock
from django.conf import settings
from django.core.cache import caches
from waffle.models import Flag

from kuma.wiki.models import Document, Revision


@pytest.fixture()
def cleared_cacheback_cache():
    caches[settings.CACHEBACK_CACHE_ALIAS].clear()
    yield
    caches[settings.CACHEBACK_CACHE_ALIAS].clear()


class ConstanceConfigWrapper(object):
    """A Constance configuration wrapper to allow overriding the config."""
    _original_values = []

    def __setattr__(self, attr, value):
        from constance import config
        self._original_values.append((attr, getattr(config, attr)))
        setattr(config, attr, value)
        # This can fail if Constance uses a cached database backend
        # CONSTANCE_DATABASE_CACHE_BACKEND = False to disable
        assert getattr(config, attr) == value

    def finalize(self):
        from constance import config
        for attr, value in reversed(self._original_values):
            setattr(config, attr, value)
        del self._original_values[:]


@pytest.fixture
def constance_config(db, settings):
    """A Constance config object which restores changes after the testrun."""
    wrapper = ConstanceConfigWrapper()
    yield wrapper
    wrapper.finalize()


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
def user_client(client, wiki_user):
    wiki_user.set_password('password')
    wiki_user.save()
    client.login(username=wiki_user.username, password='password')
    return client


@pytest.fixture
def editor_client(user_client):
    Flag.objects.create(name='kumaediting', everyone=True)
    return user_client


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
def mock_requests():
    with requests_mock.Mocker() as mocker:
        yield mocker
