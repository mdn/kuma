from django import http, test
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_
from pyquery import PyQuery as pq
import test_utils


def mockdekiauth(test):
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    def test_new(self, authenticate, get_user):
        authenticate.return_value = self.testuser
        get_user.return_value = self.testuser
        self.client.login(authtoken='1')
        test(self)
    return test_new


class DemoViewsTest(test_utils.TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.testuser = User.objects.get(username='testuser')

    def test_submit_loggedout(self):
        r = self.client.get(reverse('demos_submit'), follow=True)
        choices = pq(r.content)('p.choices')
        eq_(choices.find('a.button').length, 2)

    @mockdekiauth
    def test_submit_loggedin(self):
        r = self.client.get(reverse('demos_submit'), follow=True)
        assert pq(r.content)('form#demo-submit')

    @mockdekiauth
    def test_submit_post_invalid(self):
        r = self.client.post('/en-US/demos/submit', data={}, follow=True)
        d = pq(r.content)
        assert d('form#demo-submit')
        assert d('li#field_title ul.errorlist')
        assert d('li#field_summary ul.errorlist')
        assert d('li#field_screenshot_1 ul.errorlist')
        assert d('li#field_demo_package ul.errorlist')
        assert d('li#field_license_name ul.errorlist')
        assert d('li#field_captcha ul.errorlist')
        assert d('li#field_accept_terms ul.errorlist')
