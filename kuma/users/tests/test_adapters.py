from nose.plugins.attrib import attr
from nose.tools import eq_, assert_raises

from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.utils.importlib import import_module
from django.test import RequestFactory

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialLogin, SocialAccount

from kuma.users.adapters import KumaSocialAccountAdapter

from . import UserTestCase


class KumaSocialAccountAdapterTestCase(UserTestCase):

    def setUp(self):
        """ extra setUp to make a working session """
        from django.conf import settings
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        self.adapter = KumaSocialAccountAdapter()

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

        # Verify the social_login receiver over-writes the provider
        # stored in the session
        self.adapter.pre_social_login(request, sociallogin)
        eq_(account.provider,
            request.session['sociallogin_provider'],
            "receiver should have over-written sociallogin_provider "
            "session variable")

    @attr('bug1063830')
    def test_pre_social_login_error_for_unmatched_login(self):
        """ https://bugzil.la/1063830 """

        # Set up a GitHub SocialLogin in the session
        github_account = SocialAccount.objects.get(user__username='testuser2')
        github_login = SocialLogin(account=github_account)

        request = RequestFactory().get('/')
        session = self.client.session
        session['socialaccount_sociallogin'] = github_login.serialize()
        session.save()
        request.session = session
        messages = self.get_messages(request)

        # Set up an un-matching Persona SocialLogin for request
        persona_account = SocialAccount(user=User(), provider='persona',
                                        uid='noone@inexistant.com')
        persona_login = SocialLogin(account=persona_account)

        assert_raises(ImmediateHttpResponse,
                      self.adapter.pre_social_login, request, persona_login)
        queued_messages = list(messages)
        eq_(len(queued_messages), 1)
        eq_(django_messages.ERROR, queued_messages[0].level)
