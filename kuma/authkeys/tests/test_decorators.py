import base64

import pytest

from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser

from kuma.authkeys.decorators import accepts_auth_key


@accepts_auth_key
def fake_view(request, foo, bar):
    return (foo, bar)


@pytest.mark.current
@pytest.mark.django_db
@pytest.mark.parametrize("maintenance_mode", [False, True])
@pytest.mark.parametrize(
    "use_valid_key, use_valid_secret",
    [(True, True), (True, False), (False, True), (False, False)]
)
def test_auth_key_decorator(user_auth_key, settings, use_valid_key,
                            use_valid_secret, maintenance_mode):
    request = HttpRequest()
    request.user = AnonymousUser()

    auth = '%s:%s' % (
        user_auth_key.key.key if use_valid_key else 'FAKE',
        user_auth_key.secret if use_valid_secret else 'FAKE'
    )

    b64_auth = base64.encodestring(auth)
    request.META['HTTP_AUTHORIZATION'] = 'Basic %s' % b64_auth

    settings.MAINTENANCE_MODE = maintenance_mode

    foo, bar = fake_view(request, 'foo', 'bar')

    assert foo == 'foo'
    assert bar == 'bar'

    if maintenance_mode or not (use_valid_key and use_valid_secret):
        assert not request.user.is_authenticated()
        assert request.authkey is None
    else:
        assert request.user.is_authenticated()
        assert request.user == user_auth_key.user
        assert request.authkey
        assert request.authkey == user_auth_key.key


@pytest.mark.current
@pytest.mark.django_db
def test_auth_key_decorator_with_invalid_header(user_auth_key, settings):
    # Test with incorrect auth header
    request = HttpRequest()
    request.user = AnonymousUser()
    request.META['HTTP_AUTHORIZATION'] = "Basic bad_auth_string"

    settings.MAINTENANCE_MODE = False

    # Make a request to the view
    fake_view(request, 'foo', 'bar')

    # The user should not be authenticated and no error should be raised.
    assert not request.user.is_authenticated()
    assert request.authkey is None
