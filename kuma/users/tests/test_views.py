import urllib

import pytest
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email", (None, "ringo@beatles.com"), ids=("without-email", "with-email")
)
def test_no_prompt_login(client, settings, email):
    params = {}
    if email:
        params.update(email=email)
    response = client.get(reverse("no_prompt_login"), data=params)
    assert response.status_code == 302
    location = response.headers.get("location")
    assert location
    location = urllib.parse.unquote(location)
    assert settings.OIDC_OP_AUTHORIZATION_ENDPOINT in location
    assert "next=/en-US/plus" in location
    if email:
        assert "prompt=none" in location
        assert f"login_hint={email}" in location
