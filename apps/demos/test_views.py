from django import http, test
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_
from pyquery import PyQuery as pq
import test_utils

class DemoViewsTest(test_utils.TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.testuser = User.objects.get(username='testuser')

    def test_submit_loggedout(self):
        r = self.client.get(reverse('demos_submit'), follow=True)
        choices = pq(r.content)('p.choices')
        eq_(choices.find('a.button').length, 2)

    # TODO: extract into a DevmoTestCase class and/or a wrapper?
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    def test_submit_loggedin(self, authenticate, get_user):
        authenticate.return_value = self.testuser
        get_user.return_value = self.testuser
        self.client.login(authtoken='1')
        r = self.client.get(reverse('demos_submit'), follow=True)
        assert pq(r.content)('form#demo-submit')
