from django import forms
from django.test import RequestFactory
import mock

from kuma.core.tests import KumaTestCase, eq_, ok_

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
        eq_(True, form.is_valid())

        # let's try this with the username above
        test_user2 = user(save=True)
        form = UserEditForm(data, instance=test_user2)
        eq_(False, form.is_valid())

    def test_can_keep_legacy_username(self):
        test_user = user(username='legacy@example.com', save=True)
        ok_(test_user.has_legacy_username)
        data = {
            'username': 'legacy@example.com'
        }
        form = UserEditForm(data, instance=test_user)
        ok_(form.is_valid(), repr(form.errors))

    def test_cannot_change_legacy_username(self):
        test_user = user(username='legacy@example.com', save=True)
        ok_(test_user.has_legacy_username)
        data = {
            'username': 'mr.legacy@example.com'
        }
        form = UserEditForm(data, instance=test_user)
        eq_(form.is_valid(), False)
        eq_(form.errors, {'username': [USERNAME_CHARACTERS]})

    def test_cannot_change_to_legacy_username(self):
        test_user = user(save=True)
        eq_(test_user.has_legacy_username, False)
        data = {
            'username': 'mr.legacy@example.com'
        }
        form = UserEditForm(data, instance=test_user)
        eq_(form.is_valid(), False)
        eq_(form.errors, {'username': [USERNAME_CHARACTERS]})

    def test_blank_username_invalid(self):
        test_user = user(save=True)
        data = {
            'username': '',
        }
        form = UserEditForm(data, instance=test_user)
        eq_(form.is_valid(), False)
        eq_(form.errors, {'username': ['This field cannot be blank.']})

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
                eq_(expected_valid, result_valid)


class AllauthUsernameTests(KumaTestCase):
    def test_email_username(self):
        """
        Trying to use an email address as a username fails, with a
        message saying an email address can't be used as a username.
        """
        bad_usernames = (
            'testuser@example.com',
            '@testuser',
        )
        adapter = KumaAccountAdapter()
        for username in bad_usernames:
            self.assertRaisesMessage(forms.ValidationError,
                                     USERNAME_EMAIL,
                                     adapter.clean_username,
                                     username)

    def test_bad_username(self):
        """
        Illegal usernames fail with our custom error message rather
        than the misleading allauth one which suggests '@' is a legal
        character.
        """
        adapter = KumaAccountAdapter()
        self.assertRaisesMessage(forms.ValidationError,
                                 USERNAME_CHARACTERS,
                                 adapter.clean_username,
                                 'dolla$dolla$bill')


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
        expected = [mock.call(user1.pk, 'en-US'), mock.call(user2.pk, 'en-US')]
        mock_send_email.assert_has_calls(expected, any_order=True)
