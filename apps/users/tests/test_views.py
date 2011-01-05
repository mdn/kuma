from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_

from notifications.models import EventWatch
from questions.models import Question, CONFIRMED, UNCONFIRMED
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.models import RegistrationProfile, EmailChange


class RegisterTestCase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    @mock.patch_object(Site.objects, 'get_current')
    def test_new_user(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username='newbie')
        assert u.password.startswith('sha256')
        assert not u.is_active
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        key = RegistrationProfile.objects.all()[0].activation_key
        assert mail.outbox[0].body.find('activate/%s' % key) > 0

        # Now try to log in
        u.is_active = True
        u.save()
        response = self.client.post(reverse('users.login', locale='en-US'),
                                    {'username': 'newbie',
                                     'password': 'foo'}, follow=True)
        eq_(200, response.status_code)
        eq_('http://testserver/en-US/home', response.redirect_chain[0][0])

    @mock.patch_object(Site.objects, 'get_current')
    def test_unicode_password(self, get_current):
        u_str = u'\xe5\xe5\xee\xe9\xf8\xe7\u6709\u52b9'
        get_current.return_value.domain = 'su.mo.com'
        response = self.client.post(reverse('users.register', locale='ja'),
                                    {'username': 'cjkuser',
                                     'email': 'cjkuser@example.com',
                                     'password': u_str,
                                     'password2': u_str}, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username='cjkuser')
        u.is_active = True
        u.save()
        assert u.password.startswith('sha256')

        # make sure you can login now
        response = self.client.post(reverse('users.login', locale='ja'),
                                    {'username': 'cjkuser',
                                     'password': u_str}, follow=True)
        eq_(200, response.status_code)
        eq_('http://testserver/ja/home', response.redirect_chain[0][0])

    @mock.patch_object(Site.objects, 'get_current')
    def test_new_user_activation(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        assert not user.is_active
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        user = User.objects.get(pk=user.pk)
        assert user.is_active

    @mock.patch_object(Site.objects, 'get_current')
    def test_new_user_with_questions(self, get_current):
        """Unconfirmed questions get confirmed with account confirmation."""
        get_current.return_value.domain = 'su.mo.com'
        # TODO: remove this test once we drop unconfirmed questions.
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')

        # Before we activate, let's create a question.
        q = Question.objects.create(title='test_question', creator=user,
                                    content='test', status=UNCONFIRMED,
                                    confirmation_id='$$$')

        # Activate account.
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        q = Question.objects.get(creator=user)
        # Question is listed on the confirmation page.
        assert 'test_question' in response.content
        assert q.get_absolute_url() in response.content
        eq_(CONFIRMED, q.status)

    def test_duplicate_username(self):
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'jsocol',
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    def test_duplicate_email(self):
        User.objects.create(username='noob', email='noob@example.com').save()
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'noob@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    def test_no_match_passwords(self):
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'bar'}, follow=True)
        self.assertContains(response, 'must match')


class ChangeEmailTestCase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.client = LocalizingClient()
        # Create some notifications
        EventWatch.objects.create(content_type_id=1, watch_id=2,
                                  email='user47963@nowhere')

    @mock.patch_object(Site.objects, 'get_current')
    def test_user_change_email(self, get_current):
        """Send email to change user's email and then change it."""
        get_current.return_value.domain = 'su.mo.com'

        self.client.login(username='pcraciunoiu', password='testpass')
        # Attempt to change email.
        response = self.client.post(reverse('users.change_email'),
                                    {'email': 'paulc@trololololololo.com'},
                                    follow=True)
        eq_(200, response.status_code)

        # Be notified to click a confirmation link.
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]
        assert ec.activation_key in mail.outbox[0].body
        eq_('paulc@trololololololo.com', ec.email)

        # Visit confirmation link to change email.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        u = User.objects.get(username='pcraciunoiu')
        eq_('paulc@trololololololo.com', u.email)

        # Notifications have been updated.
        # TODO: remove this after notifications model is updated.
        ew = EventWatch.objects.get()
        eq_('paulc@trololololololo.com', ew.email)
