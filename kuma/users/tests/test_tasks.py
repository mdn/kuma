import mock
from nose.tools import eq_, ok_
from waffle import Switch

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import RequestFactory

from allauth.account.models import EmailAddress
from allauth.account.signals import user_signed_up

from kuma.users.tasks import send_welcome_email

from . import UserTestCase, user


class TestWelcomeEmails(UserTestCase):

    def test_default_language_email(self):
        u = User.objects.get(username='testuser')
        send_welcome_email(u.pk, settings.WIKI_DEFAULT_LANGUAGE)

        welcome_email = mail.outbox[0]
        expected_to = [u.email]
        eq_(expected_to, welcome_email.to)
        ok_(u'utm_campaign=welcome' in welcome_email.body)

    @mock.patch('devmo.utils.strings_are_translated')
    def test_dont_send_untranslated_language_email(self,
                                                   strings_are_translated):
        strings_are_translated.return_value = False
        u = User.objects.get(username='testuser')
        send_welcome_email(u.pk, 'tlh')  # Qapla'
        eq_([], mail.outbox)

        send_welcome_email(u.pk, 'de')  # Servus
        eq_(1, len(mail.outbox))

    def test_welcome_mail_for_verified_email(self):
        Switch.objects.get_or_create(name='welcome_email', active=True)
        u = user(username='welcome',
                 email='welcome@tester.com',
                 password='welcome',
                 save=True)
        request = RequestFactory().get('/')
        request.locale = 'en-US'
        user_signed_up.send(sender=u.__class__, request=request, user=u)

        # no email sent
        eq_(len(mail.outbox), 0)

        EmailAddress.objects.create(user=u,
                                    email='welcome@tester.com',
                                    verified=True)

        user_signed_up.send(sender=u.__class__, request=request, user=u)

        # only one email, the welcome email, is sent, no confirmation needed
        eq_(len(mail.outbox), 1)
        welcome_email = mail.outbox[0]
        expected_to = [u.email]
        eq_(expected_to, welcome_email.to)
        ok_(u'utm_campaign=welcome' in welcome_email.body)

    def test_welcome_mail_for_unverified_email(self):
        Switch.objects.get_or_create(name='welcome_email', active=True)
        u = user(username='welcome2',
                 email='welcome2@tester.com',
                 password='welcome2',
                 save=True)
        email_address = EmailAddress.objects.create(user=u,
                                                    email='welcome2@tester.com',
                                                    verified=False)
        request = RequestFactory().get('/')
        request.locale = 'en-US'

        # emulate the phase in which the request for email confirmation is
        # sent as the user's email address is not verified
        email_address.send_confirmation(request)

        # only one email, the confirmation email is sent
        eq_(1, email_address.emailconfirmation_set.count())
        eq_(len(mail.outbox), 1)
        confirm_email = mail.outbox[0]
        expected_to = [email_address.email]
        eq_(expected_to, confirm_email.to)
        ok_('Confirm' in confirm_email.subject)

        # then get the email confirmation and confirm it by emulating
        # clicking on the confirm link
        email_confirmation = email_address.emailconfirmation_set.all()[0]
        email_confirmation.confirm(request)

        # a second email, the welcome email, is sent
        eq_(len(mail.outbox), 2)
        welcome_email = mail.outbox[1]
        expected_to = [email_address.email]
        eq_(expected_to, welcome_email.to)
        ok_('utm_campaign=welcome' in welcome_email.body)

        # now add second unverified email address to the user
        # and check if the usual confirmation email is sent out
        email_address2 = EmailAddress.objects.create(user=u,
                                                     email='welcome3@tester.com',
                                                     verified=False)
        email_address2.send_confirmation(request)
        eq_(1, email_address2.emailconfirmation_set.count())
        eq_(len(mail.outbox), 3)
        confirm_email2 = mail.outbox[2]
        expected_to = [email_address2.email]
        eq_(expected_to, confirm_email2.to)
        ok_('Confirm' in confirm_email2.subject)

        # but this time there should no welcome email be sent as there
        # is already a verified email address
        email_confirmation2 = email_address2.emailconfirmation_set.all()[0]
        email_confirmation2.confirm(request)
        # no increase in number of emails
        eq_(len(mail.outbox), 3)
        ok_('Confirm' in mail.outbox[2].subject)
