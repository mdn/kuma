import pytest

from kuma.users.models import AccountEvent, UserProfile
from kuma.users.tasks import process_event_subscription_state_change


@pytest.mark.django_db
def test_process_event_subscription_state_change(wiki_user):

    profile = UserProfile.objects.create(user=wiki_user)
    assert profile.subscription_type == ""

    created_event = AccountEvent.objects.create(
        event_type=AccountEvent.EventType.SUBSCRIPTION_CHANGED,
        status=AccountEvent.EventStatus.PENDING,
        fxa_uid=wiki_user.username,
        id=1,
        payload='{"capabilities": ["mdn_plus_5y"], "isActive": true}',
    )

    process_event_subscription_state_change(created_event.id)
    profile.refresh_from_db()
    assert profile.subscription_type == "mdn_plus_5y"


@pytest.mark.django_db
def test_empty_subscription_inactive_change(wiki_user):

    profile = UserProfile.objects.create(user=wiki_user)
    assert profile.subscription_type == ""

    created_event = AccountEvent.objects.create(
        event_type=AccountEvent.EventType.SUBSCRIPTION_CHANGED,
        status=AccountEvent.EventStatus.PENDING,
        fxa_uid=wiki_user.username,
        id=1,
        payload='{"capabilities": [], "isActive": false}',
    )

    process_event_subscription_state_change(created_event.id)
    profile.refresh_from_db()
    assert profile.subscription_type == ""
    assert profile.is_subscriber == False


@pytest.mark.django_db
def test_valid_subscription_inactive_change(wiki_user):

    profile = UserProfile.objects.create(user=wiki_user)
    assert profile.subscription_type == ""

    created_event = AccountEvent.objects.create(
        event_type=AccountEvent.EventType.SUBSCRIPTION_CHANGED,
        status=AccountEvent.EventStatus.PENDING,
        fxa_uid=wiki_user.username,
        id=1,
        payload='{"capabilities": ["mdn_plus_5m"], "isActive": false}',
    )

    process_event_subscription_state_change(created_event.id)
    profile.refresh_from_db()
    assert profile.subscription_type == ""
    assert profile.is_subscriber == False


@pytest.mark.django_db
def test_invalid_subscription_change(wiki_user):

    profile = UserProfile.objects.create(user=wiki_user)
    assert profile.subscription_type == ""

    created_event = AccountEvent.objects.create(
        event_type=AccountEvent.EventType.SUBSCRIPTION_CHANGED,
        status=AccountEvent.EventStatus.PENDING,
        fxa_uid=wiki_user.username,
        id=1,
        payload='{"capabilities": ["invalid_subscription"], "isActive": true}',
    )

    process_event_subscription_state_change(created_event.id)
    profile.refresh_from_db()
    assert profile.subscription_type == ""


@pytest.mark.django_db
def test_multiple_valid_subscription_change_takes_first_in_array(wiki_user):

    profile = UserProfile.objects.create(user=wiki_user)
    assert profile.subscription_type == ""

    created_event = AccountEvent.objects.create(
        event_type=AccountEvent.EventType.SUBSCRIPTION_CHANGED,
        status=AccountEvent.EventStatus.PENDING,
        fxa_uid=wiki_user.username,
        id=1,
        payload='{"capabilities": ["mdn_plus", "mdn_plus_5y", "mdn_plus_5m"], "isActive": true}',
    )

    process_event_subscription_state_change(created_event.id)
    profile.refresh_from_db()
    # Ensure only first (lexicographical) valid is persisted
    assert profile.subscription_type == "mdn_plus_5m"
