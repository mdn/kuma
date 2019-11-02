from unittest import mock

import pytest

from django import forms
from django.test import RequestFactory

from kuma.core.tests import call_on_commit_immediately, KumaTestCase

from . import user
from ..adapters import (KumaAccountAdapter, USERNAME_CHARACTERS,
                        USERNAME_EMAIL)
from ..forms import UserEditForm, UserRecoveryEmailForm
from ..models import User


class TestUserEditForm(KumaTestCase):

    def test_username(self):
        """bug 753563: Support username changes"""
        test_user = user(save=True)
        data = {
            'username': test_user.username,
        }
        form = UserEditForm(data, instance=test_user)
        assert form.is_valid()

        # let's try this with the username above
        test_user2 = user(save=True)
        form = UserEditForm(data, instance=test_user2)
        assert not form.is_valid()

    def test_can_keep_legacy_username(self):
        test_user = user(username='legacy@example.com', save=True)
        assert test_user.has_legacy_username
        data = {
            'username': 'legacy@example.com'
        }
        form = UserEditForm(data, instance=test_user)
        assert form.is_valid(), repr(form.errors)

    def test_cannot_change_legacy_username(self):
        test_user = user(username='legacy@example.com', save=True)
        assert test_user.has_legacy_username
        data = {
            'username': 'mr.legacy@example.com'
        }
        form = UserEditForm(data, instance=test_user)
        assert not form.is_valid()
        assert {'username': [USERNAME_CHARACTERS]} == form.errors

    def test_cannot_change_to_legacy_username(self):
        test_user = user(save=True)
        assert not test_user.has_legacy_username
        data = {
            'username': 'mr.legacy@example.com'
        }
        form = UserEditForm(data, instance=test_user)
        assert not form.is_valid()
        assert {'username': [USERNAME_CHARACTERS]} == form.errors

    def test_blank_username_invalid(self):
        test_user = user(save=True)
        data = {
            'username': '',
        }
        form = UserEditForm(data, instance=test_user)
        assert not form.is_valid()
        assert {'username': ['This field cannot be blank.']} == form.errors

    def test_https_user_urls(self):
        """bug 733610: User URLs should allow https"""
        protos = (
            ('http://', True),
            ('ftp://', False),
            ('gopher://', False),
            ('https://', True),
        )
        sites = (
            ('twitter', 'twitter.com/lmorchard'),
            ('github', 'github.com/lmorchard'),
            ('stackoverflow', 'stackoverflow.com/users/testuser'),
            ('linkedin', 'www.linkedin.com/in/testuser'),
        )
        self._assert_protos_and_sites(protos, sites)

    def test_linkedin_public_user_urls(self):
        """
        Bug 719651 - User field validation for LinkedIn is not
        valid for international users
        https://bugzil.la/719651
        """
        protos = (
            ('http://', True),
            ('https://', True),
        )
        sites = (
            ('linkedin', 'www.linkedin.com/in/testuser'),
            ('linkedin', 'www.linkedin.com/pub/testuser/0/1/826')
        )
        self._assert_protos_and_sites(protos, sites)

    def _assert_protos_and_sites(self, protos, sites):
        edit_user = user(save=True)
        for proto, expected_valid in protos:
            for name, site in sites:
                url = '%s%s' % (proto, site)
                data = {
                    'username': edit_user.username,
                    'email': 'lorchard@mozilla.com',
                    '%s_url' % name: url,
                }
                form = UserEditForm(data, instance=edit_user)
                result_valid = form.is_valid()
                assert expected_valid == result_valid


@pytest.mark.parametrize('username', ('testuser@example.com', '@testuser'))
def test_adapter_clean_username(username):
    """Emails can not be usernames, raising a custom error message."""
    adapter = KumaAccountAdapter()
    with pytest.raises(forms.ValidationError) as excinfo:
        adapter.clean_username(username)
    assert str(USERNAME_EMAIL) in str(excinfo.value)


def test_adapter_clean_username_invalid_characters():
    """Some letters can't be in usernames, raising a custom error message."""
    adapter = KumaAccountAdapter()
    with pytest.raises(forms.ValidationError) as excinfo:
        adapter.clean_username('dolla$dolla$bill')
    assert str(USERNAME_CHARACTERS) in str(excinfo.value)


@mock.patch('kuma.users.forms.send_recovery_email')
class UserRecoveryEmailFormTests(KumaTestCase):

    factory = RequestFactory()

    def test_send_no_emails(self, mock_send_email):
        email = 'no-one@example.com'
        assert not User.objects.filter(email=email).exists()
        form = UserRecoveryEmailForm(data={'email': email})
        request = self.factory.post('/en-US/account/recover/send')
        assert form.is_valid()
        form.save(request)
        mock_send_email.assert_not_called()

    def test_send_two_emails(self, mock_send_email):
        email = 'two@example.com'
        user1 = User.objects.create(username='user1', email=email)
        user2 = User.objects.create(username='user2', email=email)
        form = UserRecoveryEmailForm(data={'email': email})
        request = self.factory.post('/en-US/account/recover/send')
        request.LANGUAGE_CODE = 'en-US'
        assert form.is_valid()
        form.save(request)
        expected = [mock.call(user1.pk, email, 'en-US'),
                    mock.call(user2.pk, email, 'en-US')]
        mock_send_email.assert_has_calls(expected, any_order=True)

    def test_send_persona_owner(self, mock_send_email):
        email = 'persona@example.com'
        user1 = User.objects.create(username='other', email='other@example.com')
        user1.socialaccount_set.create(provider='persona', uid=email)
        form = UserRecoveryEmailForm(data={'email': email})
        request = self.factory.post('/en-US/account/recover/send')
        request.LANGUAGE_CODE = 'en-US'
        assert form.is_valid()
        form.save(request)
        mock_send_email.assert_called_once_with(user1.pk, email, 'en-US')

    @call_on_commit_immediately
    def test_send_confirmed_email(self, mock_send_email):
        email = 'confirmed@example.com'
        user1 = User.objects.create(username='other', email='other@example.com')
        user1.emailaddress_set.create(email=email)
        form = UserRecoveryEmailForm(data={'email': email})
        request = self.factory.post('/en-US/account/recover/send')
        request.LANGUAGE_CODE = 'en-US'
        assert form.is_valid()
        form.save(request)
        mock_send_email.assert_called_once_with(user1.pk, email, 'en-US')
