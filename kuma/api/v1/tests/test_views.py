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


@pytest.mark.django_db
@override_flag("subscription", True)
@mock.patch("kuma.users.newsletter.tasks.create_or_update_contact.delay")
@mock.patch("kuma.users.stripe_utils.stripe")
def test_create_subscription_success(
    mocked_stripe,
    mock_create_or_update_newsletter_contact_delay,
    wiki_user,
    user_client,
):

    mock_customer = mock.MagicMock()
    mock_customer.id = "cus_1234"
    mock_customer.subscriptions.list().auto_paging_iter().__iter__.return_value = []
    mocked_stripe.Customer.create.return_value = mock_customer

    mock_subscription = mock.MagicMock()
    subscription_id = "sub_1234"
    mock_subscription.id = subscription_id
    mocked_stripe.Subscription.create.return_value = mock_subscription

    response = user_client.post(
        reverse("api.v1.subscriptions"),
        content_type="application/json",
        data={"stripe_token": "tok_visa"},
    )
    assert response.status_code == 201
    assert UserSubscription.objects.filter(stripe_subscription_id=subscription_id)
    mock_create_or_update_newsletter_contact_delay.assert_called_once_with(wiki_user.pk)


@pytest.mark.django_db
@override_flag("subscription", True)
def test_subscriptions_without_login(client):
    response = client.post(reverse("api.v1.subscriptions"))
    assert response.status_code == 403
    response = client.get(reverse("api.v1.subscriptions"))
    assert response.status_code == 403


@pytest.mark.django_db
@override_flag("subscription", False)
def test_subscription_with_disabled_waffle(user_client):
    response = user_client.post(reverse("api.v1.subscriptions"))
    assert response.status_code == 403
    response = user_client.get(reverse("api.v1.subscriptions"))
    assert response.status_code == 403


@pytest.mark.django_db
@override_flag("subscription", True)
def test_list_subscriptions_no_stripe_customer_id(user_client):
    response = user_client.get(reverse("api.v1.subscriptions"))
    assert response.status_code == 200
    assert response.json()["subscriptions"] == []


@mock.patch("kuma.users.stripe_utils.stripe")
@pytest.mark.django_db
@override_flag("subscription", True)
def test_list_subscriptions_customer_no_subscription(mocked_stripe, stripe_user_client):
    mock_customer = mock.MagicMock()
    mock_customer.id = "cus_1234"
    mock_customer.subscriptions.list().auto_paging_iter().__iter__.return_value = []
    mocked_stripe.Customer.retrieve.return_value = mock_customer
    response = stripe_user_client.get(reverse("api.v1.subscriptions"))
    assert response.status_code == 200
    assert response.json()["subscriptions"] == []


@pytest.mark.django_db
@override_flag("subscription", True)
def test_list_subscriptions_not_customer(user_client):
    response = user_client.get(reverse("api.v1.subscriptions"))
    assert response.status_code == 200
    assert response.json()["subscriptions"] == []


@mock.patch("kuma.users.stripe_utils.stripe")
@pytest.mark.django_db
@override_flag("subscription", True)
def test_list_subscriptions_with_active_subscription(
    mocked_stripe, stripe_user_client, settings
):
    mock_subscription_items = mock.MagicMock()
    mock_subscription_item = mock.MagicMock()
    mock_subscription_item.plan = mock.MagicMock()
    mock_subscription_item.plan.id = settings.STRIPE_PLAN_ID
    mock_subscription_item.plan.amount = 500
    mock_subscription_items.auto_paging_iter().__iter__.return_value = [
        mock_subscription_item
    ]
    mock_subscription = mock.MagicMock()
    mock_subscription.id = "sub_1234"
    mock_subscription.plan.amount = 500
    mock_subscription.__getitem__.return_value = mock_subscription_items

    mock_customer = mock.MagicMock()
    mock_customer.id = "cus_1234"
    mock_customer.subscriptions.list().auto_paging_iter().__iter__.return_value = [
        mock_subscription
    ]
    mock_customer.default_source.object = "card"
    mock_customer.default_source.brand = "Amex"
    mock_customer.default_source.exp_month = 12
    mock_customer.default_source.exp_year = 23
    mock_customer.default_source.last4 = 6789
    mock_customer.default_source.get.return_value = "29466"
    now_timestamp = int(time.time())
    mock_customer.default_source.next_payment_at = now_timestamp
    mocked_stripe.Customer.retrieve.return_value = mock_customer
    response = stripe_user_client.get(reverse("api.v1.subscriptions"))
    assert response.status_code == 200
    assert response.json()["subscriptions"][0]["amount"] == 500
    assert response.json()["subscriptions"][0]["id"] == "sub_1234"


@mock.patch("kuma.users.newsletter.tasks.create_or_update_contact.delay")
@mock.patch("kuma.users.stripe_utils.stripe")
@pytest.mark.django_db
@override_flag("subscription", True)
def test_cancel_subscriptions_with_active_subscription(
    mocked_stripe,
    mock_create_or_update_newsletter_contact_delay,
    stripe_user_client,
    wiki_user,
):
    subscription_id = "sub_1234"
    mock_subscription = mock.MagicMock()
    mock_subscription.id = subscription_id
    mocked_stripe.Customer.retrieve().subscriptions.data.__iter__.return_value = [
        mock_subscription
    ]
    mocked_stripe.Subscription.retrieve.return_value = mock_subscription
    response = stripe_user_client.delete(reverse("api.v1.subscriptions"))
    assert response.status_code == 204
    assert UserSubscription.objects.get(stripe_subscription_id=subscription_id).canceled

    mock_create_or_update_newsletter_contact_delay.assert_called_once_with(wiki_user.pk)


@mock.patch("kuma.users.stripe_utils.stripe")
@pytest.mark.django_db
@override_flag("subscription", True)
def test_cancel_subscriptions_with_no_active_subscription(
    mocked_stripe, stripe_user_client
):
    mocked_stripe.Customer.retrieve().subscriptions.data.__iter__.return_value = []
    response = stripe_user_client.delete(reverse("api.v1.subscriptions"))
    assert response.status_code == 410


@mock.patch("kuma.api.v1.views._download_from_url")
@mock.patch("kuma.api.v1.views.retrieve_and_synchronize_subscription_info")
@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_payment_succeeded_sends_invoice_mail(
    construct_stripe_event, retrieve_subscription, download_url
):
    construct_stripe_event.return_value = SimpleNamespace(
        type="invoice.payment_succeeded",
        data=SimpleNamespace(
            object=SimpleNamespace(
                number="test_invoice_001",
                total=700,
                customer="cus_mock_testuser",
                created=1583842724,
                invoice_pdf="https://developer.mozilla.org/mock-invoice-pdf-url",
            )
        ),
    )
    retrieve_subscription.return_value = {
        "next_payment_at": 1583842724,
        "brand": "MagicCard",
    }
    download_url.return_value = bytes("totally not a pdf", "utf-8")

    testuser = create_user(
        save=True,
        username="testuser",
        email="testuser@example.com",
        stripe_customer_id="cus_mock_testuser",
    )
    response = Client().post(
        reverse("api.v1.stripe_hooks"),
        content_type="application/json",
        data={},
    )
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    payment_email = mail.outbox[0]
    assert payment_email.to == [testuser.email]
    assert "Receipt" in payment_email.subject
    assert "Invoice number: test_invoice_001" in payment_email.body
    assert "You supported MDN with a $7.00 monthly subscription" in payment_email.body
    assert "Manage monthly subscription" in payment_email.body


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


@mock.patch("kuma.api.v1.views._send_payment_received_email")
@mock.patch("kuma.api.v1.views.track_event")
@mock.patch("stripe.Event.construct_from")
@pytest.mark.django_db
def test_stripe_payment_succeeded_sends_ga_tracking(
    mock1, track_event_mock_signals, mock2, client, settings
):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = True

    mock1.return_value = SimpleNamespace(
        type="invoice.payment_succeeded",
        data=SimpleNamespace(
            object=SimpleNamespace(
                customer="cus_mock_testuser",
                created=1583842724,
                invoice_pdf="https://developer.mozilla.org/mock-invoice-pdf-url",
            )
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
        CATEGORY_MONTHLY_PAYMENTS,
        ACTION_SUBSCRIPTION_CREATED,
        f"{settings.CONTRIBUTION_AMOUNT_USD:.2f}",
    )


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


@mock.patch("kuma.users.newsletter.tasks.create_or_update_contact.delay")
@mock.patch("kuma.users.stripe_utils.stripe")
def test_account_settings_delete_with_subscription(
    mocked_stripe,
    mock_create_or_update_newsletter_contact_delay,
    user_client,
    wiki_user,
):
    subscription_id = "sub_1234"
    mock_subscription = mock.MagicMock()
    mock_subscription.id = subscription_id
    mock_customer = mock.MagicMock()
    mock_customer.subscriptions.data.__iter__.return_value = [mock_subscription]
    mocked_stripe.Customer.retrieve.return_value = mock_customer
    mocked_stripe.Subscription.retrieve.return_value = mock_subscription

    # Also, pretend that the user has a rich profile
    wiki_user.stripe_customer_id = "cus_12345"
    wiki_user.save()
    UserSubscription.set_active(wiki_user, subscription_id)

    wiki_user.is_newsletter_subscribed = False
    wiki_user.save()

    username = wiki_user.username
    response = user_client.delete(reverse("api.v1.settings"))
    assert response.status_code == 200
    assert not User.objects.filter(username=username).exists()
    assert not UserSubscription.objects.filter(stripe_subscription_id="sub_1234")


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
