import mock

from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from allauth.account.signals import user_signed_up
from django.conf import settings
from django.contrib import messages as django_messages
from django.core import mail
from django.test import RequestFactory, TestCase
from waffle.testutils import override_switch

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.users.tasks import send_recovery_email, send_welcome_email

from . import user, UserTestCase


class SendRecoveryEmailTests(TestCase):
    def test_send_email(self):
        testuser = user(username='legacy', email='legacy@example.com')
        testuser.set_unusable_password()
        testuser.save()
        send_recovery_email(testuser.pk, email='actual@example.com')
        testuser.refresh_from_db()
        assert not testuser.has_usable_password()
        recovery_url = testuser.get_recovery_url()
        assert len(mail.outbox) == 1
        recovery_email = mail.outbox[0]
        assert recovery_email.to == ['actual@example.com']
        assert recovery_url in recovery_email.body
        assert testuser.username in recovery_email.subject


class TestWelcomeEmails(UserTestCase):
    rf = RequestFactory()

    def setup_request_for_messages(self):
        request = self.rf.get('/')
        request.LANGUAGE_CODE = 'en-US'
        session = self.client.session
        session.save()
        request.session = session
        return request

    def test_default_language_email(self):
        testuser = self.user_model.objects.get(username='testuser')
        send_welcome_email(testuser.pk, settings.WIKI_DEFAULT_LANGUAGE)

        welcome_email = mail.outbox[0]
        expected_to = [testuser.email]
        self.assertEqual(expected_to, welcome_email.to)
        self.assertTrue(u'utm_campaign=welcome' in welcome_email.body)

    @mock.patch('kuma.users.tasks.strings_are_translated')
    def test_dont_send_untranslated_language_email(self,
                                                   strings_are_translated):
        strings_are_translated.return_value = False
        testuser = self.user_model.objects.get(username='testuser')
        send_welcome_email(testuser.pk, 'en-NZ')
        self.assertEqual([], mail.outbox)

        strings_are_translated.return_value = True
        send_welcome_email(testuser.pk, 'en-NZ')
        self.assertEqual(1, len(mail.outbox))

    @override_switch('welcome_email', True)
    def test_welcome_mail_for_verified_email(self):
        testuser = user(username='welcome', email='welcome@tester.com',
                        password='welcome', save=True)
        request = self.setup_request_for_messages()
        self.get_messages(request)
        user_signed_up.send(sender=testuser.__class__, request=request,
                            user=testuser)

        # no email sent
        self.assertEqual(len(mail.outbox), 0)

        EmailAddress.objects.create(user=testuser,
                                    email='welcome@tester.com',
                                    verified=True)

        user_signed_up.send(sender=testuser.__class__, request=request,
                            user=testuser)

        # only one email, the welcome email, is sent, no confirmation needed
        self.assertEqual(len(mail.outbox), 1)
        welcome_email = mail.outbox[0]
        expected_to = [testuser.email]
        self.assertEqual(expected_to, welcome_email.to)
        self.assertTrue(u'utm_campaign=welcome' in welcome_email.body)

    def test_signup_getting_started_message(self):
        testuser = user(username='welcome', email='welcome@tester.com',
                        password='welcome', save=True)
        request = self.setup_request_for_messages()
        messages = self.get_messages(request)
        self.assertEqual(len(messages), 0)

        user_signed_up.send(sender=testuser.__class__, request=request,
                            user=testuser)

        queued_messages = list(messages)
        self.assertEqual(len(queued_messages), 1)
        self.assertEqual(django_messages.SUCCESS, queued_messages[0].level)
        self.assertTrue('getting started' in queued_messages[0].message)

    @override_switch('welcome_email', True)
    def test_welcome_mail_for_unverified_email(self):
        testuser = user(username='welcome2', email='welcome2@tester.com',
                        password='welcome2', save=True)
        email_address = EmailAddress.objects.create(user=testuser,
                                                    email='welcome2@tester.com',
                                                    verified=False)
        request = self.rf.get('/')
        request.LANGUAGE_CODE = 'en-US'

        # emulate the phase in which the request for email confirmation is
        # sent as the user's email address is not verified
        confirmation = EmailConfirmationHMAC(email_address)
        confirmation.send()

        # only one email, the confirmation email is sent
        self.assertEqual(len(mail.outbox), 1)
        confirm_email = mail.outbox[0]
        expected_to = [email_address.email]
        self.assertEqual(expected_to, confirm_email.to)
        self.assertTrue('Confirm' in confirm_email.subject)

        # Click on a similar confirm link (HMAC has timestamp, changes)
        link = reverse('account_confirm_email', args=[confirmation.key])
        resp = self.client.get(link)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        resp = self.client.post(link)
        assert resp.status_code == 302
        assert_no_cache_header(resp)

        # a second email, the welcome email, is sent
        self.assertEqual(len(mail.outbox), 2)
        welcome_email = mail.outbox[1]
        expected_to = [email_address.email]
        self.assertEqual(expected_to, welcome_email.to)
        self.assertTrue('utm_campaign=welcome' in welcome_email.body)

        # now add second unverified email address to the user
        # and check if the usual confirmation email is sent out
        email_address2 = EmailAddress.objects.create(user=testuser,
                                                     email='welcome3@tester.com',
                                                     verified=False)
        confirmation2 = EmailConfirmationHMAC(email_address2)
        confirmation2.send()
        self.assertEqual(len(mail.outbox), 3)
        confirm_email2 = mail.outbox[2]
        expected_to = [email_address2.email]
        self.assertEqual(expected_to, confirm_email2.to)
        self.assertTrue('Confirm' in confirm_email2.subject)

        # Confirm the second email address
        link2 = reverse('account_confirm_email', args=[confirmation2.key])
        resp = self.client.get(link2)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        resp = self.client.post(link2)
        assert resp.status_code == 302
        assert_no_cache_header(resp)

        # no increase in number of emails (no 2nd welcome email)
        self.assertEqual(len(mail.outbox), 3)
        self.assertTrue('Confirm' in mail.outbox[2].subject)
