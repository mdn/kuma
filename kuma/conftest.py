from datetime import datetime

import pytest
import requests_mock
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import caches
from django.urls import set_urlconf
from django.utils.translation import activate
from waffle.testutils import override_flag

from kuma.core.urlresolvers import reverse
from kuma.wiki.constants import REDIRECT_CONTENT
from kuma.wiki.models import Document, Revision


@pytest.fixture(autouse=True)
def set_default_language():
    activate('en-US')


@pytest.fixture(autouse=True)
def disable_s3(settings):
    """
    Disable S3 when running tests just in case it's enabled for manual testing.
    """
    settings.MDN_API_S3_BUCKET_NAME = None


@pytest.fixture(autouse=True)
def reset_urlconf():
    """
    Reset the default urlconf used by "reverse" to the one provided
    by settings.ROOT_URLCONF.

    Django resets the default urlconf back to settings.ROOT_URLCONF at
    the beginning of each request, but if the incoming request has a
    "urlconf" attribute, the default urlconf is changed to its value for
    the remainder of the request, so that all subsequent "reverse" calls
    use that value (unless they explicitly specify a different one). The
    problem occurs when a test is run that uses the "request.urlconf"
    mechanism, setting the default urlconf to something other than
    settings.ROOT_URLCONF, and then subsequent tests make "reverse" calls
    that fail because they're expecting a default urlconf of
    settings.ROOT_URLCONF (i.e., they're not explicitly providing a
    urlconf value to the "reverse" call).
    """
    set_urlconf(None)
    yield
    set_urlconf(None)


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
def beta_testers_group(db):
    return Group.objects.create(name='Beta Testers')


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
    """A test client with wiki_user logged in."""
    wiki_user.set_password('password')
    wiki_user.save()
    client.login(username=wiki_user.username, password='password')
    return client


@pytest.fixture
def editor_client(user_client):
    """A test client with wiki_user logged in for editing."""
    with override_flag('kumaediting', True):
        yield user_client


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


@pytest.fixture
def trans_doc(create_revision, wiki_user):
    """Translate the root document into French."""
    trans_doc = Document.objects.create(
        locale='fr',
        parent=create_revision.document,
        slug='Racine',
        title='Racine du Document')
    Revision.objects.create(
        document=trans_doc,
        creator=wiki_user,
        based_on=create_revision,
        content='<p>Mise en route...</p>',
        title='Racine du Document',
        created=datetime(2017, 4, 14, 12, 20))
    return trans_doc


@pytest.fixture
def redirect_doc(wiki_user, root_doc):
    """A newly-created top-level English redirect document."""
    redirect_doc = Document.objects.create(
        locale='en-US', slug='Redirection', title='Redirect Document')
    Revision.objects.create(
        document=redirect_doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {
            'href': reverse('wiki.document', args=(root_doc.slug,)),
            'title': root_doc.title,
        },
        title='Redirect Document',
        created=datetime(2017, 4, 17, 12, 15))
    return redirect_doc


@pytest.fixture
def mock_requests():
    with requests_mock.Mocker() as mocker:
        yield mocker
