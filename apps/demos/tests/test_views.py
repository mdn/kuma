from django import http, test
from django.conf import settings
from django.contrib.auth.models import User

from sumo.urlresolvers import reverse
from sumo.tests import LocalizingClient

from mock import patch
from nose.tools import eq_
from pyquery import PyQuery as pq
import test_utils

from test_models import save_valid_submission


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
        self.client = LocalizingClient()

    def test_submit_loggedout(self):
        r = self.client.get(reverse('demos_submit'))
        choices = pq(r.content)('p.choices')
        eq_(choices.find('a.button').length, 2)

    @mockdekiauth
    def test_submit_loggedin(self):
        r = self.client.get(reverse('demos_submit'))
        assert pq(r.content)('form#demo-submit')

    @mockdekiauth
    def test_submit_post_invalid(self):
        r = self.client.post('/en-US/demos/submit', data={})
        d = pq(r.content)
        assert d('form#demo-submit')
        assert d('li#field_title ul.errorlist')
        assert d('li#field_summary ul.errorlist')
        assert d('li#field_screenshot_1 ul.errorlist')
        assert d('li#field_demo_package ul.errorlist')
        assert d('li#field_license_name ul.errorlist')
        assert d('li#field_captcha ul.errorlist')
        assert d('li#field_accept_terms ul.errorlist')

    def test_detail(self):
        s = save_valid_submission('hello world')

        url = reverse('demos_detail', args=[s.slug])
        r = self.client.get(url)
        d = pq(r.content)
        a = d('a[href="%s"]' % url)
        eq_(s.title, a.text())
        eq_(s.title, d('h1.page-title').text())
        edit_link = d('ul.manage a.edit')
        assert not edit_link

    @mockdekiauth
    def test_creator_can_edit(self):
        s = save_valid_submission('hello world')

        url = reverse('demos_detail', args=[s.slug])
        r = self.client.get(url)
        d = pq(r.content)
        edit_link = d('ul.manage a.edit')
        assert edit_link
        edit_url = reverse('demos_edit', args=[s.slug], locale='en-US')
        eq_(edit_url, edit_link.attr("href"))

        r = self.client.get(edit_url)
        assert pq(r.content)('form#demo-submit')
        eq_('Save changes', pq(r.content)('p.fm-submit button[type="submit"]').text())

    @mockdekiauth
    def test_hidden_field(self):
        s = save_valid_submission('hello world')

        edit_url = reverse('demos_edit', args=[s.slug], locale='en-US')
        r = self.client.get(edit_url)
        assert pq(r.content)('input[name="hidden"][type="checkbox"]')

    @mockdekiauth
    def test_derby_field(self):
        s = save_valid_submission('hello world')

        edit_url = reverse('demos_edit', args=[s.slug], locale='en-US')
        r = self.client.get(edit_url)
        assert pq(r.content)('fieldset#devderby-submit')
