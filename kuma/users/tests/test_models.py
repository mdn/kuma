from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from kuma.wiki.tests import revision
from ..models import UserBan, UserProfile
from . import profile, UserTestCase


class TestUserProfile(UserTestCase):

    def test_user_profile(self):
        """user.profile returns what you'd expect."""
        user = self.user_model.objects.all()[0]
        p = profile(user)

        eq_(p, user.profile)

    def test_websites(self):
        """A list of websites can be maintained on a UserProfile"""
        user = self.user_model.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)

        # Property should start off as an empty dict()
        sites = profile.websites
        eq_({}, sites)

        # Assemble a set of test sites.
        test_sites = dict(
            website='http://example.com',
            twitter='http://twitter.com/lmorchard',
            github='http://github.com/lmorchard',
            stackoverflow='http://stackoverflow.com/users/lmorchard',
            linkedin='https://www.linkedin.com/in/testuser',
            mozillians='https://mozillians.org/u/testuser',
            facebook='https://www.facebook.com/test.user'
        )

        # Try a mix of assignment cases for the websites property
        sites['website'] = test_sites['website']
        sites['bad'] = 'bad'
        del sites['bad']
        profile.websites['twitter'] = test_sites['twitter']
        profile.websites.update(dict(
            github=test_sites['github'],
            stackoverflow=test_sites['stackoverflow'],
            linkedin=test_sites['linkedin'],
            mozillians=test_sites['mozillians'],
            facebook=test_sites['facebook'],
        ))

        # Save and make sure a fresh fetch works as expected
        profile.save()
        p2 = UserProfile.objects.get(user=user)
        eq_(test_sites, p2.websites)

        # One more set-and-save to be sure this survives a round-trip
        test_sites['google'] = 'http://google.com'
        p2.websites['google'] = test_sites['google']
        p2.save()
        p3 = UserProfile.objects.get(user=user)
        eq_(test_sites, p3.websites)

    def test_irc_nickname(self):
        """We've added IRC nickname as a profile field.
        Make sure it shows up."""
        user = self.user_model.objects.get(username='testuser')
        profile_from_db = UserProfile.objects.get(user=user)
        ok_(hasattr(profile_from_db, 'irc_nickname'))
        eq_('testuser', profile_from_db.irc_nickname)

    def test_unicode_email_gravatar(self):
        """Bug 689056: Unicode characters in email addresses shouldn't break
        gravatar URLs"""
        user = self.user_model.objects.get(username='testuser')
        user.email = u"Someguy Dude\xc3\xaas Lastname"
        try:
            profile = UserProfile.objects.get(user=user)
            profile.gravatar
        except UnicodeEncodeError:
            self.fail("There should be no UnicodeEncodeError")

    def test_locale_timezone_fields(self):
        """We've added locale and timezone fields. Verify defaults."""
        user = self.user_model.objects.get(username='testuser')
        profile_from_db = UserProfile.objects.get(user=user)
        ok_(hasattr(profile_from_db, 'locale'))
        ok_(profile_from_db.locale == 'en-US')
        ok_(hasattr(profile_from_db, 'timezone'))
        ok_(str(profile_from_db.timezone) == 'US/Pacific')

    def test_wiki_activity(self):
        user = self.user_model.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        rev = revision(save=True, is_approved=True)
        ok_(rev.pk in profile.wiki_activity().values_list('pk', flat=True))


class BanTestCase(UserTestCase):

    @attr('bans')
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
        ok_(testuser_banned.profile.is_banned)
        ok_(testuser_banned.profile.active_ban().by == admin)

        ban.is_active = False
        ban.save()
        testuser_unbanned = self.user_model.objects.get(username='testuser')
        ok_(testuser_unbanned.is_active)

        ban.is_active = True
        ban.save()
        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)
        ok_(testuser_unbanned.profile.is_banned)
        ok_(testuser_unbanned.profile.active_ban())

        ban.delete()
        testuser_unbanned = self.user_model.objects.get(username='testuser')
        ok_(testuser_unbanned.is_active)
        ok_(not testuser_unbanned.profile.is_banned)
        ok_(testuser_unbanned.profile.active_ban() is None)
