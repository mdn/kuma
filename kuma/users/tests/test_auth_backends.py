import pytest

from ..auth_backends import KumaAuthBackend
from ..models import User, UserBan


@pytest.fixture()
def test_user(db):
    user = User.objects.create(username="user", email="user@example.com")
    user.set_password("password")
    user.save()
    return user


def test_auth_unknown_user(db):
    assert not User.objects.filter(id=666).exists()
    assert KumaAuthBackend().get_user(666) is None


def test_auth_unbanned_user(test_user):
    user = KumaAuthBackend().get_user(test_user.id)
    assert user == test_user


def test_auth_banned_user(test_user, admin_user):
    UserBan.objects.create(
        user=test_user, by=admin_user, reason="Banned by unit test.", is_active=True
    )
    assert KumaAuthBackend().get_user(test_user.id) is None
