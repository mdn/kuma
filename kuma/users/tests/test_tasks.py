from unittest import mock

from allauth.account.models import EmailAddress
from allauth.account.signals import user_signed_up
from django.conf import settings
from django.core import mail
from django.test import RequestFactory
from waffle.testutils import override_switch

from kuma.core.tests import call_on_commit_immediately
from kuma.users.tasks import send_welcome_email

from . import create_user, UserTestCase


class TestWelcomeEmails(UserTestCase):
    rf = RequestFactory()

    def setup_request_for_messages(self):
        request = self.rf.get("/")
        request.LANGUAGE_CODE = "en-US"
        session = self.client.session
        session.save()
        request.session = session
        return request

    def test_default_language_email(self):
        testuser = self.user_model.objects.get(username="testuser")
        send_welcome_email(testuser.pk, settings.WIKI_DEFAULT_LANGUAGE)

        welcome_email = mail.outbox[0]
        expected_to = [testuser.email]
        self.assertEqual(expected_to, welcome_email.to)

    @mock.patch("kuma.users.tasks.strings_are_translated")
    def test_dont_send_untranslated_language_email(self, strings_are_translated):
        strings_are_translated.return_value = False
        testuser = self.user_model.objects.get(username="testuser")
        send_welcome_email(testuser.pk, "en-NZ")
        self.assertEqual([], mail.outbox)

        strings_are_translated.return_value = True
        send_welcome_email(testuser.pk, "en-NZ")
        self.assertEqual(1, len(mail.outbox))

    @override_switch("welcome_email", True)
    @call_on_commit_immediately
    def test_welcome_mail_for_verified_email(self):
        testuser = create_user(
            username="welcome",
            email="welcome@tester.com",
            password="welcome",
            save=True,
        )
        request = self.setup_request_for_messages()
        user_signed_up.send(sender=testuser.__class__, request=request, user=testuser)

        # no email sent
        self.assertEqual(len(mail.outbox), 0)

        EmailAddress.objects.create(
            user=testuser, email="welcome@tester.com", verified=True
        )

        user_signed_up.send(sender=testuser.__class__, request=request, user=testuser)

        # only one email, the welcome email, is sent, no confirmation needed
        self.assertEqual(len(mail.outbox), 1)
        welcome_email = mail.outbox[0]
        expected_to = [testuser.email]
        self.assertEqual(expected_to, welcome_email.to)
