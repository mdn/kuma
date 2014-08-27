import mock
from nose.tools import eq_, ok_

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail

from kuma.users.tasks import send_welcome_email
from sumo.tests import TestCase


class TestWelcomeEmails(TestCase):
    fixtures = ['test_users.json']

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
        send_welcome_email(u.pk, 'de')

        eq_([], mail.outbox)
