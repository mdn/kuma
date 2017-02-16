import pytest


@pytest.mark.current
@pytest.mark.django_db
def test_secret_generation(user_auth_key):
    """Generated secret should be saved as a hash and pass a check"""
    key = user_auth_key.key
    secret = user_auth_key.secret
    assert key.key
    assert key.hashed_secret
    assert len(key.hashed_secret) > 0
    assert len(secret) > 0
    assert secret != key.hashed_secret
    assert not key.check_secret("I AM A FAKE")
    assert key.check_secret(secret)
