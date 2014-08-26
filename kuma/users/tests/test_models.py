from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils.importlib import import_module

import test_utils
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from allauth.socialaccount.models import SocialLogin, SocialAccount

from devmo.tests import LocalizingClient
from kuma.wiki.tests import revision
from sumo.tests import TestCase
from ..models import UserBan, UserProfile, on_pre_social_login
from . import profile


class TestUserProfile(test_utils.TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        pass

    def test_user_get_profile(self):
        """user.get_profile() returns what you'd expect."""
        user = User.objects.all()[0]
        p = profile(user)

        eq_(p, user.get_profile())

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

    def test_wiki_activity(self):
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        revision(save=True, is_approved=True)
        eq_(1, len(profile.wiki_activity()))


class BanTestCase(TestCase):
    fixtures = ['test_users.json']

    @attr('bans')
    def test_ban_user(self):
        testuser = User.objects.get(username='testuser')
        admin = User.objects.get(username='admin')
        ok_(testuser.is_active)
        ban = UserBan(user=testuser,
                      by=admin,
                      reason='Banned by unit test')
        ban.save()
        testuser_banned = User.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        ban.is_active = False
        ban.save()
        testuser_unbanned = User.objects.get(username='testuser')
        ok_(testuser_unbanned.is_active)


class SocialAccountSignalReceiverTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        """ extra setUp to make a working session """
        from django.conf import settings
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.client = LocalizingClient()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    @attr('bug1055870')
    def test_pre_social_login_overwrites_session_var(self):
        """ https://bugzil.la/1055870 """
        # Set up a pre-existing GitHub sign-in session
        request = RequestFactory().get('/')
        session = self.client.session
        session['sociallogin_provider'] = 'github'
        session.save()
        request.session = session

        # Set up a Persona SocialLogin
        account = SocialAccount.objects.get(user__username='testuser')
        sociallogin = SocialLogin(account=account)
        sender = SocialLogin

        # Verify the social_login receiver over-writes the provider
        # stored in the session
        on_pre_social_login(sender=sender, request=request,
                            sociallogin=sociallogin)
        eq_(account.provider,
            request.session['sociallogin_provider'],
            "receiver should have over-written sociallogin_provider "
            "session variable")
