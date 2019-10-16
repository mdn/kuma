import json

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from waffle.testutils import override_flag

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.spam.akismet import Akismet
from kuma.spam.constants import SPAM_SUBMISSIONS_FLAG, SPAM_URL, VERIFY_URL

from ..models import RevisionAkismetSubmission


@pytest.fixture
def permission_add_revisionakismetsubmission(db):
    return Permission.objects.get(codename='add_revisionakismetsubmission')


@pytest.fixture
def akismet_wiki_user(wiki_user, permission_add_revisionakismetsubmission):
    """A user with "add_revisionakismetsubmission" permission."""
    wiki_user.user_permissions.add(permission_add_revisionakismetsubmission)
    return wiki_user


@pytest.fixture
def akismet_wiki_user_2(wiki_user_2, permission_add_revisionakismetsubmission):
    """A second user with "add_revisionakismetsubmission" permission."""
    wiki_user_2.user_permissions.add(permission_add_revisionakismetsubmission)
    return wiki_user_2


@pytest.fixture
def akismet_mock_requests(mock_requests):
    mock_requests.post(VERIFY_URL, content='valid')
    mock_requests.post(SPAM_URL, content=Akismet.submission_success)
    return mock_requests


@pytest.fixture
def enable_akismet_submissions(constance_config):
    constance_config.AKISMET_KEY = 'dashboard'
    with override_flag(SPAM_SUBMISSIONS_FLAG, True):
        yield constance_config


@pytest.mark.spam
@pytest.mark.parametrize(
    'http_method', ['get', 'put', 'delete', 'options', 'head'])
def test_disallowed_methods(db, client, http_method):
    """HTTP methods other than POST are not allowed."""
    url = reverse('wiki.submit_akismet_spam')
    response = getattr(client, http_method)(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.spam
def test_spam_valid_response(create_revision, akismet_wiki_user, user_client,
                             enable_akismet_submissions,
                             akismet_mock_requests):
    url = reverse('wiki.submit_akismet_spam')
    response = user_client.post(url, data={'revision': create_revision.id},
                                HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 201
    assert_no_cache_header(response)

    # One RevisionAkismetSubmission record should exist for this revision.
    ras = RevisionAkismetSubmission.objects.get(revision=create_revision)
    assert ras.type == u'spam'

    # Check that the Akismet endpoints were called.
    assert akismet_mock_requests.called
    assert akismet_mock_requests.call_count == 2

    data = json.loads(response.content)
    assert len(data) == 1
    assert data[0]['sender'] == akismet_wiki_user.username
    assert data[0]['type'] == u'spam'


@pytest.mark.spam
def test_spam_with_many_response(create_revision, akismet_wiki_user,
                                 akismet_wiki_user_2, user_client,
                                 enable_akismet_submissions,
                                 akismet_mock_requests):
    submission = RevisionAkismetSubmission(
        type="ham",
        sender=akismet_wiki_user_2,
        revision=create_revision
    )
    submission.save()

    # Check that one RevisionAkismetSubmission instance exists.
    ras = RevisionAkismetSubmission.objects.filter(revision=create_revision)
    assert ras.count() == 1

    # Create another Akismet revision via the endpoint.
    url = reverse('wiki.submit_akismet_spam')
    response = user_client.post(url, data={'revision': create_revision.id},
                                HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 201
    assert_no_cache_header(response)
    data = json.loads(response.content)
    assert len(data) == 2
    assert data[0]['type'] == 'ham'
    assert data[0]['sender'] == akismet_wiki_user_2.username
    assert data[1]['type'] == 'spam'
    assert data[1]['sender'] == akismet_wiki_user.username

    # Check that the Akismet endpoints were called.
    assert akismet_mock_requests.called
    assert akismet_mock_requests.call_count == 2


@pytest.mark.spam
def test_spam_no_permission(create_revision, wiki_user, user_client,
                            enable_akismet_submissions, akismet_mock_requests):
    url = reverse('wiki.submit_akismet_spam')
    response = user_client.post(url, data={'revision': create_revision.id},
                                HTTP_HOST=settings.WIKI_HOST)
    # Redirects to login page when without permission.
    assert response.status_code == 302
    assert response['Location'].endswith('users/signin?next={}'.format(url))
    assert_no_cache_header(response)

    # No RevisionAkismetSubmission record should exist.
    ras = RevisionAkismetSubmission.objects.filter(revision=create_revision)
    assert ras.count() == 0

    # Check that the Akismet endpoints were not called.
    assert not akismet_mock_requests.called


@pytest.mark.spam
def test_spam_revision_does_not_exist(create_revision, akismet_wiki_user,
                                      user_client, enable_akismet_submissions,
                                      akismet_mock_requests):
    revision_id = create_revision.id
    create_revision.delete()

    url = reverse('wiki.submit_akismet_spam')
    response = user_client.post(url, data={'revision': revision_id},
                                HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 400
    assert_no_cache_header(response)

    # No RevisionAkismetSubmission record should exist.
    ras = RevisionAkismetSubmission.objects.filter(revision_id=revision_id)
    assert ras.count() == 0

    # Check that the Akismet endpoints were not called.
    assert not akismet_mock_requests.called
