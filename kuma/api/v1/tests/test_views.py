import time
from types import SimpleNamespace
from unittest import mock

import pytest
from django.core import mail
from django.test import Client
from stripe.error import APIError
from waffle.models import Flag, Switch
from waffle.testutils import override_flag

from kuma.attachments.models import Attachment, AttachmentRevision
from kuma.core.ga_tracking import (
    ACTION_SUBSCRIPTION_CANCELED,
    ACTION_SUBSCRIPTION_CREATED,
    ACTION_SUBSCRIPTION_FEEDBACK,
    CATEGORY_MONTHLY_PAYMENTS,
)
from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.users.models import User, UserBan, UserSubscription
from kuma.users.tests import create_user
from kuma.wiki.models import DocumentDeletionLog


@pytest.mark.parametrize("http_method", ["put", "post", "delete", "options", "head"])
def test_whoami_disallowed_methods(client, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse("api.v1.whoami")
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_whoami_anonymous(client):
    """Test response for anonymous users."""
    # Create some fake waffle objects
    Flag.objects.create(name="vip_only", authenticated=True)
    Flag.objects.create(name="flag_all", everyone=True)
    Flag.objects.create(name="flag_none", percent=0)
    Switch.objects.create(name="switch_on", active=True)
    Switch.objects.create(name="switch_off", active=False)

    url = reverse("api.v1.whoami")
    response = client.get(url)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert response.json() == {}
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_whoami_anonymous_cloudfront_geo(client):
    """Test response for anonymous users."""
    url = reverse("api.v1.whoami")
    response = client.get(url, HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME="US of A")
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert response.json()["geo"] == {"country": "US of A"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_staff,is_superuser,is_beta_tester",
    [(False, False, False), (True, True, True)],
    ids=("muggle", "wizard"),
)
def test_whoami(
    user_client,
    wiki_user,
    wiki_user_github_account,
    beta_testers_group,
    is_staff,
    is_superuser,
    is_beta_tester,
):
    """Test responses for logged-in users."""
    # First delete all flags created from data migrations
    Flag.objects.all().delete()

    # Create some fake waffle objects
    Flag.objects.create(name="vip_only", authenticated=True)
    Flag.objects.create(name="flag_all", everyone=True)
    Flag.objects.create(name="flag_none", percent=0, superusers=False)
    Switch.objects.create(name="switch_on", active=True)
    Switch.objects.create(name="switch_off", active=False)

    wiki_user.is_staff = is_staff
    wiki_user.is_superuser = is_superuser
    wiki_user.is_staff = is_staff
    if is_beta_tester:
        wiki_user.groups.add(beta_testers_group)
    wiki_user.save()
    url = reverse("api.v1.whoami")
    response = user_client.get(url)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    expect = {
        "username": wiki_user.username,
        "is_authenticated": True,
        "avatar_url": wiki_user_github_account.get_avatar_url(),
        "subscriber_number": None,
        "email": "wiki_user@example.com",
    }
    if is_staff:
        expect["is_staff"] = True
    if is_superuser:
        expect["is_superuser"] = True
    if is_beta_tester:
        expect["is_beta_tester"] = True

    assert response.json() == expect
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_whoami_subscriber(
    user_client,
    wiki_user,
):
    """Test responses for logged-in users and whether they have an active
    subscription."""
    url = reverse("api.v1.whoami")
    response = user_client.get(url)
    assert response.status_code == 200
    assert "is_subscriber" not in response.json()

    UserSubscription.set_active(wiki_user, "abc123")
    response = user_client.get(url)
    assert response.status_code == 200
    assert response.json()["is_subscriber"] is True
    assert response.json()["subscriber_number"] == 1

    UserSubscription.set_canceled(wiki_user, "abc123")
    response = user_client.get(url)
    assert response.status_code == 200
    assert "is_subscriber" not in response.json()
    assert response.json()["subscriber_number"] == 1


@mock.patch("kuma.api.v1.views.track_event")
@pytest.mark.django_db
@override_flag("subscription", True)
def test_send_subscriptions_feedback(track_event_mock_signals, client, settings):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = True

    response = client.post(
        reverse("api.v1.send_subscriptions_feedback"),
        content_type="application/json",
        data={"feedback": "my feedback"},
    )
    assert response.status_code == 204

    track_event_mock_signals.assert_called_with(
        CATEGORY_MONTHLY_PAYMENTS,
        ACTION_SUBSCRIPTION_FEEDBACK,
        "my feedback",
    )


@pytest.mark.django_db
@override_flag("subscription", True)
def test_send_subscriptions_feedback_failure(client, settings):
    response = client.post(
        reverse("api.v1.send_subscriptions_feedback"),
        content_type="application/json",
        data={},
    )

    assert response.status_code == 400
    assert response.content.decode(response.charset) == "no feedback"


@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_subscription_canceled(mock1, client):
    mock1.return_value = SimpleNamespace(
        type="customer.subscription.deleted",
        data=SimpleNamespace(
            object=SimpleNamespace(customer="cus_mock_testuser", id="sub_123456789")
        ),
    )

    testuser = create_user(
        save=True,
        username="testuser",
        email="testuser@example.com",
        stripe_customer_id="cus_mock_testuser",
    )
    UserSubscription.set_active(testuser, "sub_123456789")
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 200
    (user_subscription,) = UserSubscription.objects.filter(user=testuser)
    assert user_subscription.canceled


@pytest.mark.django_db
def test_stripe_hook_invalid_json(client):
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data="{not valid!",
    )
    assert response.status_code == 400


@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_hook_unexpected_type(mock1, client):
    mock1.return_value = SimpleNamespace(
        type="not.expected",
        data=SimpleNamespace(foo="bar"),
    )
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 400


@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_hook_stripe_api_error(mock1, client):
    mock1.side_effect = APIError("badness")
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 400


@mock.patch("kuma.api.v1.views.track_event")
@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_subscription_canceled_sends_ga_tracking(
    mock1, track_event_mock_signals, client
):
    mock1.return_value = SimpleNamespace(
        type="customer.subscription.deleted",
        data=SimpleNamespace(
            object=SimpleNamespace(customer="cus_mock_testuser", id="sub_123456789")
        ),
    )

    create_user(
        save=True,
        username="testuser",
        email="testuser@example.com",
        stripe_customer_id="cus_mock_testuser",
    )
    response = client.post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 200

    track_event_mock_signals.assert_called_with(
        CATEGORY_MONTHLY_PAYMENTS, ACTION_SUBSCRIPTION_CANCELED, "webhook"
    )


@pytest.mark.django_db
def test_account_settings_auth(client):
    url = reverse("api.v1.settings")
    response = client.get(url)
    assert response.status_code == 403
    response = client.delete(url)
    assert response.status_code == 403
    response = client.post(url, {})
    assert response.status_code == 403


def test_account_settings_delete(user_client, wiki_user):
    username = wiki_user.username
    response = user_client.delete(reverse("api.v1.settings"))
    assert response.status_code == 200
    assert not User.objects.filter(username=username).exists()


# DELETE this test once all the Wiki models are deleted.
def test_account_settings_delete_legacy(user_client, wiki_user, root_doc):
    # Imagine if the user still has a bunch of Wiki related models to their
    # name. That should not block the deletion.
    revision = root_doc.revisions.first()
    assert revision.creator == wiki_user

    document_deletion_log = DocumentDeletionLog.objects.create(
        locale="any", slug="Any/Thing", user=wiki_user, reason="..."
    )
    throwaway_user = User.objects.create(username="throwaway")
    user_ban_by = UserBan.objects.create(user=throwaway_user, by=wiki_user)
    user_ban_user = UserBan.objects.create(
        user=wiki_user,
        by=throwaway_user,
        is_active=False,  # otherwise it logs the user out
    )

    attachment_revision = AttachmentRevision(
        attachment=Attachment.objects.create(title="test attachment"),
        file="some/path.ext",
        mime_type="application/kuma",
        creator=wiki_user,
        title="test attachment",
    )
    attachment_revision.save()
    assert AttachmentRevision.objects.filter(creator=wiki_user).exists()
    username = wiki_user.username
    response = user_client.delete(reverse("api.v1.settings"))
    assert response.status_code == 200
    assert not User.objects.filter(username=username).exists()

    # Moved to anonymous user
    document_deletion_log.refresh_from_db()
    assert document_deletion_log.user.username == "Anonymous"
    user_ban_by.refresh_from_db()
    assert user_ban_by.by.username == "Anonymous"
    user_ban_user.refresh_from_db()
    assert user_ban_user.user.username == "Anonymous"


def test_get_and_set_settings_happy_path(user_client):
    url = reverse("api.v1.settings")
    response = user_client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    assert response.json()["locale"] == "en-US"

    response = user_client.post(url, {"locale": "zh-CN"})
    assert response.status_code == 200

    response = user_client.get(url)
    assert response.status_code == 200
    assert response.json()["locale"] == "zh-CN"

    # You can also omit certain things and things won't be set
    response = user_client.post(url, {})
    assert response.status_code == 200
    response = user_client.get(url)
    assert response.status_code == 200
    assert response.json()["locale"] == "zh-CN"


def test_set_settings_validation_errors(user_client):
    url = reverse("api.v1.settings")
    response = user_client.post(url, {"locale": "never heard of"})
    assert response.status_code == 400
    assert response.json()["errors"]["locale"][0]["code"] == "invalid_choice"
    assert response.json()["errors"]["locale"][0]["message"]
