import pytest

from kuma.core.tests import eq_, ok_
from kuma.wiki.tests import revision

from . import UserTestCase
from ..models import UserBan
from ..templatetags.jinja_helpers import gravatar_url


class TestUser(UserTestCase):

    def test_websites(self):
        """A list of websites can be maintained on a user"""
        user = self.user_model.objects.get(username='testuser')

        # Assemble a set of test sites.
        test_sites = {
            'website_url': 'http://example.com',
            'twitter_url': 'http://twitter.com/lmorchard',
            'github_url': 'http://github.com/lmorchard',
            'stackoverflow_url': 'http://stackoverflow.com/users/lmorchard',
            'mozillians_url': 'https://mozillians.org/u/testuser',
            'facebook_url': 'https://www.facebook.com/test.user'
        }

        # Try a mix of assignment cases for the websites property
        for name, url in test_sites.items():
            setattr(user, name, url)

        # Save and make sure a fresh fetch works as expected
        user.save()
        user2 = self.user_model.objects.get(pk=user.pk)
        for name, url in test_sites.items():
            eq_(getattr(user2, name), url)

    def test_linkedin_urls(self):
        user = self.user_model.objects.get(username='testuser')

        linkedin_urls = [
            'https://in.linkedin.com/in/testuser',
            'https://www.linkedin.com/in/testuser',
            'https://www.linkedin.com/pub/testuser',
        ]

        for url in linkedin_urls:
            user.linkedin_url = url
            user.save()
            new_user = self.user_model.objects.get(pk=user.pk)
            eq_(url, new_user.linkedin_url)

    def test_irc_nickname(self):
        """We've added IRC nickname as a profile field.
        Make sure it shows up."""
        user = self.user_model.objects.get(username='testuser')
        ok_(hasattr(user, 'irc_nickname'))
        eq_('testuser', user.irc_nickname)

    def test_unicode_email_gravatar(self):
        """Bug 689056: Unicode characters in email addresses shouldn't break
        gravatar URLs"""
        user = self.user_model.objects.get(username='testuser')
        user.email = u"Someguy Dude\xc3\xaas Lastname"
        try:
            gravatar_url(user.email)
        except UnicodeEncodeError:
            self.fail("There should be no UnicodeEncodeError")

    def test_locale_timezone_fields(self):
        """We've added locale and timezone fields. Verify defaults."""
        user = self.user_model.objects.get(username='testuser')
        ok_(hasattr(user, 'locale'))
        ok_(user.locale == 'en-US')
        ok_(hasattr(user, 'timezone'))
        eq_(user.timezone, 'US/Pacific')

    def test_wiki_revisions(self):
        user = self.user_model.objects.get(username='testuser')
        rev = revision(save=True, is_approved=True)
        ok_(rev.pk in user.wiki_revisions().values_list('pk', flat=True))

    def test_recovery_email(self):
        user = self.user_model.objects.get(username='testuser')
        user.set_unusable_password()
        user.save()
        url = user.get_recovery_url()
        assert url
        assert user.has_usable_password()

        # The same URL is returned on second call
        user.refresh_from_db()
        url2 = user.get_recovery_url()
        assert url == url2


class BanTestCase(UserTestCase):

    @pytest.mark.bans
    def test_ban_user(self):
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')
        ok_(testuser.is_active)
        ban = UserBan(user=testuser,
                      by=admin,
                      reason='Banned by unit test')
        ban.save()
        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)
        ok_(testuser_banned.active_ban.by == admin)

        ban.is_active = False
        ban.save()
        testuser_unbanned = self.user_model.objects.get(username='testuser')
        ok_(testuser_unbanned.is_active)

        ban.is_active = True
        ban.save()
        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)
        ok_(testuser_unbanned.active_ban)

        ban.delete()
        testuser_unbanned = self.user_model.objects.get(username='testuser')
        ok_(testuser_unbanned.is_active)
        ok_(testuser_unbanned.active_ban is None)
