from django import forms
from nose.tools import eq_, ok_

from kuma.core.tests import KumaTestCase

from . import user
from ..adapters import USERNAME_CHARACTERS, USERNAME_EMAIL, KumaAccountAdapter
from ..forms import UserEditForm


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
            ('website', 'mozilla.org'),
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
