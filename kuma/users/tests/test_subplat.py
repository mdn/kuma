import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_subscribe_redirect(client, settings):
    response = client.get(
        reverse("kuma.users.subplat.subscribe"),
    )
    assert response.status_code == 302
    assert response.url == settings.SUBSCRIPTION_SUBSCRIBE_URL


@pytest.mark.django_db
def test_settings_redirect(client, settings):
    response = client.get(
        reverse("kuma.users.subplat.settings"),
    )
    assert response.status_code == 302
    assert response.url == settings.SUBSCRIPTION_SETTINGS_URL


@pytest.mark.django_db
def test_download_redirect(client, settings):
    response = client.get(
        reverse("kuma.users.subplat.download"),
    )
    assert response.status_code == 302
    assert settings.OIDC_OP_AUTHORIZATION_ENDPOINT in response.url
    assert "prompt=none" in response.url
