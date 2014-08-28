from django.conf import settings

from nose.tools import eq_
import test_utils

from ..forms import UserProfileEditForm


class TestUserProfileEditForm(test_utils.TestCase):

    def test_https_profile_urls(self):
        """bug 733610: Profile URLs should allow https"""
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

    def test_linkedin_public_profile_urls(self):
        """
        Bug 719651 - Profile field validation for LinkedIn is not
        valid for international profiles
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
        for proto, expected_valid in protos:
            for name, site in sites:
                url = '%s%s' % (proto, site)
                form = UserProfileEditForm({
                    "email": "lorchard@mozilla.com",
                    "websites_%s" % name: url
                })
                result_valid = form.is_valid()
                eq_(expected_valid, result_valid)
