import pytest

from kuma.users.tests import user
from kuma.authkeys.models import Key


class Object(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


@pytest.fixture
@pytest.mark.django_db
def user_auth_key():
    u = user(username="test23", email="test23@example.com", save=True)
    key = Key(user=u)
    secret = key.generate_secret()
    key.save()

    return Object(
        user=u,
        key=key,
        secret=secret,
    )
