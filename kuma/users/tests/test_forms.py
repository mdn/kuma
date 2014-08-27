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
            ('stackoverflow', 'stackoverflow.com/users/lmorchard'),
            ('linkedin', 'www.linkedin.com/in/lmorchard'),
        )
        for proto, expected_valid in protos:
            for name, site in sites:
                url = '%s%s' % (proto, site)
                form = UserProfileEditForm({
                    "email": "lorchard@mozilla.com",
                    "websites_%s" % name: url
                })
                result_valid = form.is_valid()
                eq_(expected_valid, result_valid)
