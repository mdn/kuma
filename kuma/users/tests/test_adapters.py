from django.contrib import messages as django_messages
from django.test import RequestFactory

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialLogin, SocialAccount

from kuma.core.tests import eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.users.adapters import KumaSocialAccountAdapter, KumaAccountAdapter

from . import UserTestCase


class KumaSocialAccountAdapterTestCase(UserTestCase):
    rf = RequestFactory()

    def setUp(self):
        """ extra setUp to make a working session """
        super(KumaSocialAccountAdapterTestCase, self).setUp()
        self.adapter = KumaSocialAccountAdapter()

    def test_pre_social_login_overwrites_session_var(self):
        """ https://bugzil.la/1055870 """
        # Set up a pre-existing GitHub sign-in session
        request = self.rf.get('/')
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

    def test_pre_social_login_error_for_unmatched_login(self):
        """ https://bugzil.la/1063830 """

        # Set up a GitHub SocialLogin in the session
        github_account = SocialAccount.objects.get(user__username='testuser2')
        github_login = SocialLogin(account=github_account,
                                   user=github_account.user)

        request = self.rf.get('/')
        session = self.client.session
        session['socialaccount_sociallogin'] = github_login.serialize()
        session.save()
        request.session = session
        messages = self.get_messages(request)

        # Set up an un-matching Persona SocialLogin for request
        persona_account = SocialAccount(user=self.user_model(),
                                        provider='persona',
                                        uid='noone@inexistant.com')
        persona_login = SocialLogin(account=persona_account)

        self.assertRaises(ImmediateHttpResponse,
                          self.adapter.pre_social_login, request, persona_login)
        queued_messages = list(messages)
        eq_(len(queued_messages), 1)
        eq_(django_messages.ERROR, queued_messages[0].level)

    def test_pre_social_login_matched_login(self):
        """
        https://bugzil.la/1063830, happy path

        A user tries to sign in with GitHub, but their GitHub email matches
        an existing Persona-backed MDN account. They follow the prompt to login
        with Persona, and the accounts are connected.
        """

        # Set up a GitHub SocialLogin in the session
        github_account = SocialAccount.objects.get(user__username='testuser2')
        github_login = SocialLogin(account=github_account,
                                   user=github_account.user)

        request = self.rf.get('/')
        session = self.client.session
        session['sociallogin_provider'] = 'github'
        session['socialaccount_sociallogin'] = github_login.serialize()
        session.save()
        request.session = session

        # Set up an matching Persona SocialLogin for request
        persona_account = SocialAccount.objects.create(
            user=github_account.user,
            provider='persona',
            uid=github_account.user.email)
        persona_login = SocialLogin(account=persona_account)

        # Verify the social_login receiver over-writes the provider
        # stored in the session
        self.adapter.pre_social_login(request, persona_login)
        session = request.session
        eq_(session['sociallogin_provider'], 'persona')

    def test_pre_social_login_same_provider(self):
        """
        pre_social_login passes if existing provider is the same.

        I'm not sure what the real-world counterpart of this is. Logging
        in with a different GitHub account? Needed for branch coverage.
        """

        # Set up a GitHub SocialLogin in the session
        github_account = SocialAccount.objects.get(user__username='testuser2')
        github_login = SocialLogin(account=github_account,
                                   user=github_account.user)

        request = self.rf.get('/')
        session = self.client.session
        session['sociallogin_provider'] = 'github'
        session['socialaccount_sociallogin'] = github_login.serialize()
        session.save()
        request.session = session

        # Set up an un-matching GitHub SocialLogin for request
        github2_account = SocialAccount(user=self.user_model(),
                                        provider='github',
                                        uid=github_account.uid + '2')
        github2_login = SocialLogin(account=github2_account)

        self.adapter.pre_social_login(request, github2_login)
        eq_(request.session['sociallogin_provider'], 'github')


class KumaAccountAdapterTestCase(UserTestCase):
    localizing_client = True
    rf = RequestFactory()

    def setUp(self):
        """ extra setUp to make a working session """
        super(KumaAccountAdapterTestCase, self).setUp()
        self.adapter = KumaAccountAdapter()

    def test_account_connected_message(self):
        """ https://bugzil.la/1054461 """
        message_template = 'socialaccount/messages/account_connected.txt'
        request = self.rf.get('/')

        # first check for the case in which the next url in the account
        # connection process is the frontpage, there shouldn't be a message
        session = self.client.session
        session['sociallogin_next_url'] = '/'
        session.save()
        request.session = session
        request.user = self.user_model.objects.get(username='testuser')
        request.LANGUAGE_CODE = 'en-US'
        messages = self.get_messages(request)

        self.adapter.add_message(request, django_messages.INFO,
                                 message_template)
        eq_(len(messages), 0)

        # secondly check for the case in which the next url in the connection
        # process is the profile edit page, there should be a message
        session = self.client.session
        next_url = reverse('users.user_edit',
                           kwargs={'username': request.user.username},
                           locale=request.LANGUAGE_CODE)
        session['sociallogin_next_url'] = next_url
        session.save()
        request.session = session
        messages = self.get_messages(request)

        self.adapter.add_message(request, django_messages.INFO,
                                 message_template)
        queued_messages = list(messages)
        eq_(len(queued_messages), 1)
        eq_(django_messages.SUCCESS, queued_messages[0].level)
        ok_('connected' in queued_messages[0].message)
