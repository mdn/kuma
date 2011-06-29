from django.conf import settings

import zipfile
import os
from os.path import basename, dirname, isfile, isdir
import logging

from django import http, test
from django.contrib.auth.models import User

from sumo.urlresolvers import reverse
from sumo.tests import LocalizingClient

from mock import patch
from nose.tools import eq_
from pyquery import PyQuery as pq
import test_utils

from StringIO import StringIO

from test_models import save_valid_submission

from demos.models import Submission
from demos.forms import SubmissionNewForm, SubmissionEditForm


SCREENSHOT_PATH = ( '%s/fixtures/screenshot_1.png' % 
        dirname(dirname(__file__)) )


def mockdekiauth(test):
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    def test_new(self, authenticate, get_user):
        authenticate.return_value = self.testuser
        get_user.return_value = self.testuser
        self.client.login(authtoken='1')
        test(self)
    return test_new

def disable_captcha(fn):
    """Disable captcha requirement during call of the decorated function"""
    def wrap(self):
        old_key = settings.RECAPTCHA_PRIVATE_KEY
        settings.RECAPTCHA_PRIVATE_KEY = ''
        rv = fn(self)
        settings.RECAPTCHA_PRIVATE_KEY = old_key
        return rv
    return wrap

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
        r = self.client.post(reverse('demos_submit'), data={})
        d = pq(r.content)
        assert d('form#demo-submit')
        assert d('li#field_title ul.errorlist')
        assert d('li#field_summary ul.errorlist')
        assert d('li#field_screenshot_1 ul.errorlist')
        assert d('li#field_demo_package ul.errorlist')
        assert d('li#field_license_name ul.errorlist')
        assert d('li#field_captcha ul.errorlist')
        assert d('li#field_accept_terms ul.errorlist')

    @mockdekiauth
    @disable_captcha
    def test_submit_post_valid(self):

        # Create a valid demo zip file
        zf_fout = StringIO()
        zf = zipfile.ZipFile(zf_fout, 'w')
        zf.writestr('index.html', """<html></html>""")
        zf.close()
    
        # Create a new file for input
        zf_fin = StringIO(zf_fout.getvalue())
        zf_fin.name = 'demo.zip'
        
        r = self.client.post(reverse('demos_submit'), data=dict(
            title='Test submission',
            summary='This is a test demo submission',
            description='Some description goes here',
            tech_tags=('tech:audio', 'tech:video', 'tech:websockets',),
            screenshot_1=open(SCREENSHOT_PATH),
            demo_package=zf_fin,
            license_name='gpl',
            accept_terms='1',
        ))

        eq_(302, r.status_code)
        assert 'Location' in r
        assert 'test-submission' in r['Location']
    
        try:
            obj = Submission.objects.get(slug='test-submission')
            eq_('Test submission', obj.title)
        except Submission.DoesNotExist:
            assert False

    @mockdekiauth
    def test_edit_invalid(self):
        s = save_valid_submission()
        edit_url = reverse('demos_edit', args=[s.slug], locale='en-US')
        r = self.client.post(edit_url, data=dict())
        d = pq(r.content)
        assert d('form#demo-submit')
        assert d('li#field_title ul.errorlist')
        assert d('li#field_summary ul.errorlist')
        assert d('li#field_license_name ul.errorlist')

    @mockdekiauth
    def test_edit_valid(self):
        s = save_valid_submission()
        edit_url = reverse('demos_edit', args=[s.slug], locale='en-US')
        r = self.client.post(edit_url, data=dict(
            title=s.title,
            summary='This is a test demo submission',
            description='Some description goes here',
            tech_tags=('tech:audio', 'tech:video', 'tech:websockets',),
            license_name='gpl',
            accept_terms='1',
        ))

        eq_(302, r.status_code)
        assert 'Location' in r
        assert 'hello-world' in r['Location']

        try:
            obj = Submission.objects.get(slug='hello-world')
            eq_('This is a test demo submission', obj.summary)
        except Submission.DoesNotExist:
            assert False

    def test_detail(self):
        s = save_valid_submission('hello world')

        url = reverse('demos_detail', args=[s.slug])
        r = self.client.get(url)
        d = pq(r.content)
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
