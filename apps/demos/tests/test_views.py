from django.conf import settings

import datetime
import zipfile
import os
from os.path import basename, dirname, isfile, isdir
import logging

from django import http, test
from django.contrib.auth.models import User

from funfactory.urlresolvers import reverse
from sumo.tests import LocalizingClient

from mock import patch
from nose.tools import eq_, assert_equal, with_setup, assert_false, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
import test_utils

import constance.config

from StringIO import StringIO

from taggit_extras.utils import parse_tags

from test_models import save_valid_submission

from demos import challenge_utils
from demos.models import Submission
from demos.forms import SubmissionNewForm, SubmissionEditForm


SCREENSHOT_PATH = ('%s/fixtures/screenshot_1.png' %
        dirname(dirname(__file__)))


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


def make_challenge_tag():
    """
    Create a dev derby challenge tag corresponding to the current
    month. Does not include the 'challenge:' namespace, so this tag is
    safe to feed to set_ns().
    
    """
    return datetime.date.today().strftime('%Y:%B').lower()

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

    @attr('demo_submit')
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

        result_tags = [t.name for t in obj.taggit_tags.all_ns('tech:')]
        result_tags.sort()
        eq_(['tech:audio', 'tech:video', 'tech:websockets'], result_tags)


    @mockdekiauth
    def test_edit_invalid(self):
        s = save_valid_submission()
        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.post(edit_url, data=dict())
        d = pq(r.content)
        assert d('form#demo-submit')
        assert d('li#field_title ul.errorlist')
        assert d('li#field_summary ul.errorlist')
        assert d('li#field_license_name ul.errorlist')

    @mockdekiauth
    def test_edit_valid(self):
        s = save_valid_submission()
        edit_url = reverse('demos_edit', args=[s.slug])
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

    def test_detail_censored(self):
        s = save_valid_submission('hello world')
        s.censored = True
        s.save()

        url = reverse('demos_detail', args=[s.slug])
        r = self.client.get(url)
        d = pq(r.content)
        eq_('Permission Denied', d('h1.page-title').text())

    def test_detail_censored_url(self):
        s = save_valid_submission('hello world')
        s.censored = True
        s.censored_url = "http://developer.mozilla.org"
        s.save()

        url = reverse('demos_detail', args=[s.slug])
        r = self.client.get(url)
        eq_(302, r.status_code)
        eq_("http://developer.mozilla.org", r['Location'])

    @mockdekiauth
    def test_creator_can_edit(self):
        s = save_valid_submission('hello world')

        url = reverse('demos_detail', args=[s.slug])
        r = self.client.get(url)
        d = pq(r.content)
        edit_link = d('ul#demo-manage a.edit')
        assert edit_link
        edit_url = reverse('demos_edit', args=[s.slug])
        eq_(edit_url, edit_link.attr("href"))

        r = self.client.get(edit_url)
        assert pq(r.content)('form#demo-submit')
        eq_('Save changes',
            pq(r.content)('p.fm-submit button[type="submit"]').text())

    @mockdekiauth
    def test_hidden_field(self):
        s = save_valid_submission('hello world')

        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.get(edit_url)
        assert pq(r.content)('input[name="hidden"][type="checkbox"]')

    @mockdekiauth
    def test_derby_field(self):
        s = save_valid_submission('hello world')
        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.get(edit_url)
        assert pq(r.content)('fieldset#devderby-submit')

    @mockdekiauth
    def test_edit_with_challenge_tag(self):
        s = save_valid_submission('hello world')
        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.post(edit_url, data=dict(
            title=s.title,
            summary='This is a test edit',
            description='Some description goes here',
            tech_tags=('tech:audio',),
            challenge_tags=parse_tags(constance.config.DEMOS_DEVDERBY_CHALLENGE_CHOICE_TAGS)[0],
            license_name='gpl',
            accept_terms='1',
        ))
        eq_(r.status_code, 302)
        r = self.client.get(edit_url)
        eq_(r.status_code, 200)

    def test_challenge_tag_to_date_parts(self):
        tag = 'challenge:2011:october'
        eq_(challenge_utils.challenge_tag_to_date_parts(tag), (2011, 10))

    def test_challenge_tag_to_end_date(self):
        tag = 'challenge:2011:october'
        eq_(challenge_utils.challenge_tag_to_end_date(tag),
            datetime.date(2011, 10, 31))
        tag = 'challenge:2011:february'
        eq_(challenge_utils.challenge_tag_to_end_date(tag),
            datetime.date(2011, 2, 28))
        tag = 'challenge:2012:february'
        eq_(challenge_utils.challenge_tag_to_end_date(tag),
            datetime.date(2012, 2, 29))

    def test_challenge_closed(self):
        open_tag = 'challenge:%s' % make_challenge_tag()
        closed_dt = datetime.date.today() - datetime.timedelta(days=32)
        closed_tag = 'challenge:%s' % closed_dt.strftime('%Y:%B').lower()
        assert not challenge_utils.challenge_closed([open_tag])
        assert challenge_utils.challenge_closed([closed_tag])

    def test_challenge_closed_model(self):
        s = save_valid_submission('hellow world')
        assert not s.challenge_closed()
        s.taggit_tags.set_ns('challenge:', make_challenge_tag())
        assert not s.challenge_closed()
        closed_dt = datetime.date.today() - datetime.timedelta(days=32)
        s.taggit_tags.set_ns('challenge:', closed_dt.strftime('%Y:%B').lower())
        assert s.challenge_closed()

    def test_derby_before_deadline(self):
        s = save_valid_submission('hello world')
        s.taggit_tags.set_ns('challenge:', make_challenge_tag())
        form = SubmissionEditForm(instance=s)
        assert 'demo_package' in form.fields
        assert 'challenge_tags' in form.fields

    def test_derby_after_deadline(self):
        s = save_valid_submission('hello world')
        closed_dt = datetime.date.today() - datetime.timedelta(days=32)
        s.taggit_tags.set_ns('challenge:', closed_dt.strftime('%Y:%B').lower())
        form = SubmissionEditForm(instance=s)
        assert 'demo_package' not in form.fields
        assert 'challenge_tags' not in form.fields

    @mockdekiauth
    def test_derby_tag_saving(self):
        """
        There's some tricky bits in the handling of editing and saving
        challenge tags; this test just exercises a cycle of edit/save
        a couple times in a row to make sure we don't go foul in
        there.
        
        """
        s = save_valid_submission('hello world')
        closed_dt = datetime.date.today() - datetime.timedelta(days=32)
        s.taggit_tags.set_ns('challenge:', closed_dt.strftime('%Y:%B').lower())
        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.get(edit_url)
        eq_(r.status_code, 200)
        
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

        r = self.client.get(edit_url)
        eq_(r.status_code, 200)

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

        r = self.client.get(edit_url)
        eq_(r.status_code, 200)
