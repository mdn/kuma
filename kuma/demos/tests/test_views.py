# -*- coding: utf-8 -*-
import datetime
from os.path import dirname
from StringIO import StringIO
import zipfile

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from constance import config

from kuma.core.urlresolvers import reverse
from kuma.core.utils import parse_tags
from kuma.users.tests import UserTestCase

from .. import challenge_utils
from ..forms import SubmissionEditForm
from ..models import Submission
from ..tests import make_users, build_submission, build_hidden_submission

from .test_models import save_valid_submission

SCREENSHOT_PATH = ('%s/fixtures/screenshot_1.png' %
                   dirname(dirname(__file__)))
TESTUSER_PASSWORD = 'trustno1'


def logged_in(test, *args, **kwargs):
    def test_new(self):
        self.client.login(username=self.testuser.username,
                          password=TESTUSER_PASSWORD)
        test(self, *args, **kwargs)
    return test_new


def make_challenge_tag():
    """
    Create a dev derby challenge tag corresponding to the current
    month. Does not include the 'challenge:' namespace, so this tag is
    safe to feed to set_ns().
    """
    return datetime.date.today().strftime('%Y:%B').lower()


class DemoListViewsTest(UserTestCase):
    localizing_client = True

    def setUp(self):
        super(DemoListViewsTest, self).setUp()
        self.user, self.admin_user, self.other_user = make_users()

    def test_all_demos_includes_hidden_for_staff(self):
        build_submission(self.user)
        build_hidden_submission(self.user)

        r = self.client.get(reverse('demos_all'))
        count = pq(r.content)('h2.count').text()
        eq_(count, "1 Demo")

        self.client.login(username=self.admin_user.username,
                          password='admint_tester')
        r = self.client.get(reverse('demos_all'))
        count = pq(r.content)('h2.count').text()
        eq_(count, "2 Demos")

    @attr('bug882709')
    def test_search_view(self):
        try:
            self.client.get(reverse('demos_search'))
        except:
            self.fail("Search should not ISE.")


class DemoViewsTest(UserTestCase):
    localizing_client = True

    def setUp(self):
        super(DemoViewsTest, self).setUp()
        self.testuser = self.user_model.objects.get(username='testuser')
        self.testuser.set_password(TESTUSER_PASSWORD)
        self.testuser.save()

    def test_submit_loggedout(self):
        r = self.client.get(reverse('demos_submit'))
        choices = pq(r.content)('p.choices a[href*="signin"]')
        eq_(choices.length, 1)

    @logged_in
    def test_submit_loggedin(self):
        r = self.client.get(reverse('demos_submit'))
        assert pq(r.content)('form#demo-submit')

    @logged_in
    def test_submit_post_invalid(self):
        r = self.client.post(reverse('demos_submit'), data={})
        d = pq(r.content)
        assert d('form#demo-submit')
        assert d('li#field_title ul.errorlist')
        assert d('li#field_summary ul.errorlist')
        assert d('li#field_screenshot_1 ul.errorlist')
        assert d('li#field_demo_package ul.errorlist')
        assert d('li#field_license_name ul.errorlist')
        assert d('li#field_accept_terms ul.errorlist')

    @logged_in
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

    @logged_in
    def test_edit_invalid(self):
        s = save_valid_submission()
        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.post(edit_url, data=dict())
        d = pq(r.content)
        assert d('form#demo-submit')
        assert d('li#field_title ul.errorlist')
        assert d('li#field_summary ul.errorlist')
        assert d('li#field_license_name ul.errorlist')

    @logged_in
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

    @logged_in
    def test_creator_can_edit(self):
        s = save_valid_submission('hello world')

        url = reverse('demos_detail', args=[s.slug])
        r = self.client.get(url)
        d = pq(r.content)
        edit_link = d('ul#demo-manage a.edit')
        assert edit_link
        edit_url = reverse('demos_edit', args=[s.slug], locale='en-US')
        eq_(edit_url, edit_link.attr("href"))

        r = self.client.get(edit_url)
        assert pq(r.content)('form#demo-submit')
        eq_('Save changes',
            pq(r.content)('p.fm-submit button[type="submit"]').text())

    @logged_in
    def test_hidden_field(self):
        s = save_valid_submission('hello world')

        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.get(edit_url)
        assert pq(r.content)('input[name="hidden"][type="checkbox"]')

    @logged_in
    def test_edit_no_tags(self):
        s = save_valid_submission('hello world')
        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.post(edit_url, data=dict(
            title=s.title,
            summary='This is a test edit',
            description='Some description goes here',
            license_name='gpl',
            accept_terms='1',
        ))
        eq_(r.status_code, 302)
        r = self.client.get(edit_url)
        eq_(r.status_code, 200)

    @logged_in
    def test_edit_with_challenge_tag(self):
        s = save_valid_submission('hello world')
        edit_url = reverse('demos_edit', args=[s.slug])
        r = self.client.post(edit_url, data=dict(
            title=s.title,
            summary='This is a test edit',
            description='Some description goes here',
            tech_tags=('tech:audio',),
            challenge_tags=parse_tags(
                config.DEMOS_DEVDERBY_CHALLENGE_CHOICE_TAGS)[0],
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

    @logged_in
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
        assert s.slug in r['Location']

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
        assert s.slug in r['Location']

        r = self.client.get(edit_url)
        eq_(r.status_code, 200)

    @attr('bug702156')
    def test_missing_screenshots_no_exceptions(self):
        """Demo with missing screenshots should not cause exceptions in
        views"""
        # Create the submission...
        s = save_valid_submission('hello world')
        s.taggit_tags.set_ns('tech:', 'javascript')
        s.featured = True
        s.save()

        # Ensure the new screenshot and thumbnail URL code works when there's a
        # screenshot present.
        try:
            self.client.get(reverse('demos_all'))
            self.client.get(reverse('demos_tag', args=['tech:javascript']))
            self.client.get(reverse('demos_detail', args=[s.slug]))
            self.client.get(reverse('demos_feed_recent', args=['atom']))
            self.client.get(reverse('demos_feed_featured', args=['json']))
        except:
            self.fail("No exceptions should have been thrown")

        # Forcibly delete the screenshot - should not be possible from
        # user-facing UI per form validation, but we should at least not throw
        # exceptions.
        s.screenshot_1.storage.delete(s.screenshot_1.name)
        s.screenshot_1 = None
        s.save()

        # Big bucks, no whammies...
        try:
            self.client.get(reverse('demos_all'))
            self.client.get(reverse('demos_tag', args=['tech:javascript']))
            self.client.get(reverse('demos_detail', args=[s.slug]))
            self.client.get(reverse('demos_feed_recent', args=['atom']))
            self.client.get(reverse('demos_feed_featured', args=['json']))
        except:
            self.fail("No exceptions should have been thrown")

    @attr('bug745902')
    def test_long_slug(self):
        """
        A title longer than 50 characters should truncate to a
        50-character slug during (python-level) save, not on DB
        insertion, so that anything that wants the slug to build a URL
        has the value that actually ends up in the DB.

        """
        s = save_valid_submission(
            "AudioVisualizer for Alternative Music Notation Systems")
        s.taggit_tags.set_ns('tech:', 'javascript')
        s.save()
        ok_(len(s.slug) == 50)
        r = self.client.get(reverse('kuma.demos.views.detail', args=(s.slug,)))
        ok_(r.status_code == 200)

    @attr('bug781823')
    def test_unicode(self):
        """
        Unicode characters in the summary or description doesn't brick the feed
        """
        s = save_valid_submission('ΦOTOS ftw', 'ΦOTOS ΦOTOS ΦOTOS')
        s.featured = 1
        s.save()
        r = self.client.get(reverse('demos_feed_featured', args=['json']))
        ok_(r.status_code == 200)

    def test_make_unique_slug(self):
        """
        Ensure that unique slugs are generated even from titles whose
        first 50 characters are identical.
        """
        s = save_valid_submission(
            "This is a really long title whose only purpose in life is to be "
            "longer than fifty characters")
        s2 = save_valid_submission(
            "This is a really long title whose only purpose in life is to be "
            "longer than fifty characters and not the same as the first title")
        s3 = save_valid_submission(
            "This is a really long title whose only purpose in life is to be "
            "longer than fifty characters and not the same as the first or "
            "second title")
        ok_(s.slug != s2.slug and s.slug != s3.slug and s2.slug != s3.slug)
