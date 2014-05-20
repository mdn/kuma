from os.path import dirname

from nose.tools import eq_, ok_
import test_utils

from django.contrib.auth.models import User

from devmo.models import UserProfile
from wiki.tests import revision

APP_DIR = dirname(dirname(__file__))
USER_DOCS_ACTIVITY_FEED_XML = ('%s/fixtures/user_docs_activity_feed.xml' %
                               APP_DIR)


class TestUserProfile(test_utils.TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        pass

    def test_websites(self):
        """A list of websites can be maintained on a UserProfile"""
        user = User.objects.get(username='testuser')
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
        user = User.objects.get(username='testuser')
        profile_from_db = UserProfile.objects.get(user=user)
        ok_(hasattr(profile_from_db, 'irc_nickname'))
        eq_('testuser', profile_from_db.irc_nickname)

    def test_unicode_email_gravatar(self):
        """Bug 689056: Unicode characters in email addresses shouldn't break
        gravatar URLs"""
        user = User.objects.get(username='testuser')
        user.email = u"Someguy Dude\xc3\xaas Lastname"
        try:
            profile = UserProfile.objects.get(user=user)
            profile.gravatar
        except UnicodeEncodeError:
            ok_(False, "There should be no UnicodeEncodeError")

    def test_locale_timezone_fields(self):
        """We've added locale and timezone fields. Verify defaults."""
        user = User.objects.get(username='testuser')
        profile_from_db = UserProfile.objects.get(user=user)
        ok_(hasattr(profile_from_db, 'locale'))
        ok_(profile_from_db.locale == 'en-US')
        ok_(hasattr(profile_from_db, 'timezone'))
        ok_(str(profile_from_db.timezone) == 'US/Pacific')

    def test_mindtouch_timezone(self):
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        eq_("-08:00", profile.mindtouch_timezone)

    def test_mindtouch_language(self):
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        eq_("en", profile.mindtouch_language)

    def test_wiki_activity(self):
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        revision(save=True, is_approved=True)
        eq_(1, len(profile.wiki_activity()))
