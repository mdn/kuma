import json

from celery import task
from django.contrib.auth import get_user_model

from kuma.users.auth import KumaOIDCAuthenticationBackend
from kuma.users.models import AccountEvent, UserProfile


@task
def process_event_delete_user(event_id):
    event = AccountEvent.objects.get(id=event_id)
    try:
        user = get_user_model().objects.get(username=event.fxa_uid)
    except get_user_model().DoesNotExist:
        return

    user.delete()

    event.status = AccountEvent.PROCESSED
    event.save()


@task
def process_event_subscription_state_change(event_id):
    event = AccountEvent.objects.get(id=event_id)
    try:
        user = get_user_model().objects.get(username=event.fxa_uid)
        profile = UserProfile.objects.get(user=user)
    except get_user_model().DoesNotExist:
        return

    payload = json.loads(event.payload)

    last_event = AccountEvent.objects.filter(
        fxa_uid=event.fxa_uid,
        status=AccountEvent.EventStatus.PROCESSED,
        event_type=AccountEvent.EventType.SUBSCRIPTION_CHANGED,
    ).first()

    if last_event:
        last_event_payload = json.loads(last_event.payload)
        if last_event_payload["changeTime"] >= payload["changeTime"]:
            event.status = AccountEvent.EventStatus.IGNORED
            event.save()
            return

    if "mdn_plus" in payload["capabilities"]:
        if payload["isActive"]:
            profile.is_subscriber = True
        else:
            profile.is_subscriber = False
        profile.save()

    event.status = AccountEvent.EventStatus.PROCESSED
    event.save()


@task
def process_event_password_change(event_id):
    event = AccountEvent.objects.get(id=event_id)
    event.status = AccountEvent.PROCESSED
    event.save()


@task
def process_event_profile_change(event_id):
    event = AccountEvent.objects.get(id=event_id)
    try:
        user = get_user_model().objects.get(username=event.fxa_uid)
        profile = UserProfile.objects.get(user=user)
    except get_user_model().DoesNotExist:
        return

    refresh_token = profile.fxa_refresh_token

    if not refresh_token:
        event.status = AccountEvent.IGNORED
        event.save()
        return

    fxa = KumaOIDCAuthenticationBackend()
    token_info = fxa.get_token(
        {
            "client_id": fxa.OIDC_RP_CLIENT_ID,
            "client_secret": fxa.OIDC_RP_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "ttl": 60 * 5,
        }
    )
    access_token = token_info.get("access_token")
    user_info = fxa.get_userinfo(access_token, None, None)
    fxa.update_user(user, user_info)

    event.status = AccountEvent.EventStatus.PROCESSED
    event.save()
