from django.contrib.auth.models import User

from users.forms import AuthenticationForm
from users.tests import TestCaseBase


class AuthenticationFormTests(TestCaseBase):
    """AuthenticationForm tests."""
    fixtures = ['users.json']

    def test_only_active(self):
        # Verify with active user
        user = User.objects.get(username='rrosario')
        assert user.is_active
        form = AuthenticationForm(data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert form.is_valid()

        # Verify with inactive user
        user.is_active = False
        user.save()
        user = User.objects.get(username='rrosario')
        assert not user.is_active
        form = AuthenticationForm(data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert not form.is_valid()

    def test_allow_inactive(self):
        # Verify with active user
        user = User.objects.get(username='rrosario')
        assert user.is_active
        form = AuthenticationForm(only_active=False,
                                  data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert form.is_valid()

        # Verify with inactive user
        user.is_active = False
        user.save()
        user = User.objects.get(username='rrosario')
        assert not user.is_active
        form = AuthenticationForm(only_active=False,
                                  data={'username': 'rrosario',
                                        'password': 'testpass'})
        assert form.is_valid()
