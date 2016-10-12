from django.contrib import messages as django_messages
from django.test import RequestFactory

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialLogin, SocialAccount

from kuma.core.tests import eq_
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

        # Set up an alternate SocialLogin
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

        # Set up an un-matching alternate SocialLogin for request
        other_account = SocialAccount(user=self.user_model(),
                                      provider='other',
                                      uid='noone@inexistant.com')
        other_login = SocialLogin(account=other_account)

        self.assertRaises(ImmediateHttpResponse,
                          self.adapter.pre_social_login, request, other_login)
        queued_messages = list(messages)
        eq_(len(queued_messages), 1)
        eq_(django_messages.ERROR, queued_messages[0].level)

    def test_pre_social_login_matched_login(self):
        """
        https://bugzil.la/1063830, happy path

        A user tries to sign in with GitHub, but their GitHub email matches
        an existing MDN account. They are prompted to TODO
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

        # Set up an matching other SocialLogin for request
        other_account = SocialAccount.objects.create(
            user=github_account.user,
            provider='other',
            uid=github_account.user.email)
        other_login = SocialLogin(account=other_account)

        # Verify the social_login receiver over-writes the provider
        # stored in the session
        self.adapter.pre_social_login(request, other_login)
        session = request.session
        eq_(session['sociallogin_provider'], 'other')

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
    message_template = 'socialaccount/messages/account_connected.txt'

    def setUp(self):
        """ extra setUp to make a working session """
        super(KumaAccountAdapterTestCase, self).setUp()
        self.adapter = KumaAccountAdapter()
        self.user = self.user_model.objects.get(username='testuser')

    def test_account_connected_message(
            self, next_url='/', has_message=False, extra_tags=''):
        """
        Test that the account connection message depends on the next URL.

        https://bugzil.la/1054461
        """
        request = self.rf.get('/')
        request.user = self.user
        session = self.client.session
        session['sociallogin_next_url'] = next_url
        session.save()
        request.session = session
        request.LANGUAGE_CODE = 'en-US'
        messages = self.get_messages(request)
        self.adapter.add_message(request, django_messages.INFO,
                                 self.message_template, extra_tags=extra_tags)

        queued_messages = list(messages)
        if has_message:
            assert len(queued_messages) == 1
            message_data = queued_messages[0]
            assert message_data.level == django_messages.SUCCESS
            assert 'connected' in message_data.message
        else:
            assert not queued_messages
        return queued_messages

    def test_account_connected_message_user_edit(self):
        """Connection message appears if the profile edit is the next page."""
        next_url = reverse('users.user_edit',
                           kwargs={'username': self.user.username},
                           locale='en-US')
        messages = self.test_account_connected_message(next_url, True)
        assert messages[0].tags == 'account success'

    def test_account_connected_message_connection_page(self):
        """Message appears on the connections page (bug 1229906)."""
        next_url = reverse('socialaccount_connections')
        self.test_account_connected_message(next_url, True)

    def test_extra_tags(self):
        """Extra tags can be added to the message."""
        next_url = reverse('socialaccount_connections')
        messages = self.test_account_connected_message(next_url, True,
                                                       extra_tags='congrats')
        assert messages[0].tags == 'congrats account success'
