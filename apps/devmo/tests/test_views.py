import datetime
import logging
import time
from os.path import dirname

import mock
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
import test_utils
from devmo.tests import create_profile

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.paginator import PageNotAnInteger

from soapbox.models import Message

from dekicompat.tests import (mock_mindtouch_login,
                              mock_get_deki_user,
                              mock_put_mindtouch_user)
from devmo.models import UserProfile, UserDocsActivityFeed

from devmo.cron import devmo_calendar_reload
from devmo.tests import mock_fetch_user_feed

from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse


TESTUSER_PASSWORD = 'testpass'
APP_DIR = dirname(dirname(__file__))
USER_DOCS_ACTIVITY_FEED_XML = ('%s/fixtures/user_docs_activity_feed.xml' %
                               APP_DIR)


class ProfileViewsTest(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client = LocalizingClient()
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    @attr('docs_activity')
    @mock_fetch_user_feed
    def test_profile_view(self):
        """A user profile can be viewed"""
        profile = UserProfile.objects.get(user__username='testuser')
        user = profile.user
        url = reverse('devmo.views.profile_view',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(profile.user.username,
            doc.find('#profile-head.vcard .nickname').text())
        eq_(profile.fullname,
            doc.find('#profile-head.vcard .fn').text())
        eq_(profile.title,
            doc.find('#profile-head.vcard .title').text())
        eq_(profile.organization,
            doc.find('#profile-head.vcard .org').text())
        eq_(profile.location,
            doc.find('#profile-head.vcard .loc').text())
        eq_('IRC: ' + profile.irc_nickname,
            doc.find('#profile-head.vcard .irc').text())
        eq_(profile.bio,
            doc.find('#profile-head.vcard .bio').text())

        # There should be 15 doc activity items in the page.
        feed_trs = doc.find('#docs-activity table.activity tbody tr')
        eq_(15, feed_trs.length)

        # Check to find all the items expected from the feed
        feed = UserDocsActivityFeed(username="Sheppy")
        for idx in range(0, 15):
            item = feed.items[idx]
            item_el = feed_trs.eq(idx)
            eq_(item.current_title, item_el.find('h3').text())
            eq_(item.view_url, item_el.find('h3 a').attr('href'))
            if item.edit_url:
                eq_(item.edit_url,
                    item_el.find('.actions a.edit').attr('href'))
            if item.diff_url:
                eq_(item.diff_url,
                    item_el.find('.actions a.diff').attr('href'))
            if item.history_url:
                eq_(item.history_url,
                    item_el.find('.actions a.history').attr('href'))

    @mock_put_mindtouch_user
    @mock_fetch_user_feed
    def test_bug_698971(self):
        """A non-numeric page number should not cause an error"""
        (user, deki_user, profile) = create_profile()

        url = '%s?page=asdf' % reverse('devmo.views.profile_view',
                                       args=(user.username,))

        try:
            self.client.get(url, follow=True)
        except PageNotAnInteger:
            ok_(False, "Non-numeric page number should not cause an error")

    @mock_put_mindtouch_user
    @mock_fetch_user_feed
    def test_profile_edit(self):
        profile = UserProfile.objects.get(user__username='testuser')
        user = profile.user
        url = reverse('devmo.views.profile_view', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(0, doc.find('#profile-head .edit .button').length)

        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('devmo.views.profile_view',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        edit_button = doc.find('#profile-head .edit .button')
        eq_(1, edit_button.length)

        url = edit_button.attr('href')
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(profile.fullname,
            doc.find('#profile-edit input[name="fullname"]').val())
        eq_(profile.title,
            doc.find('#profile-edit input[name="title"]').val())
        eq_(profile.organization,
            doc.find('#profile-edit input[name="organization"]').val())
        eq_(profile.location,
            doc.find('#profile-edit input[name="location"]').val())
        eq_(profile.irc_nickname,
            doc.find('#profile-edit input[name="irc_nickname"]').val())

        new_attrs = dict(
            email="tester23@example.com",
            fullname="Another Name",
            title="Another title",
            organization="Another org",
        )

        r = self.client.post(url, new_attrs, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('#profile-head').length)
        eq_(new_attrs['fullname'],
            doc.find('#profile-head .main .fn').text())
        eq_(new_attrs['title'],
            doc.find('#profile-head .info .title').text())
        eq_(new_attrs['organization'],
            doc.find('#profile-head .info .org').text())

        profile = UserProfile.objects.get(user__username=user.username)
        eq_(new_attrs['fullname'], profile.fullname)
        eq_(new_attrs['title'], profile.title)
        eq_(new_attrs['organization'], profile.organization)

    @mock_put_mindtouch_user
    @mock_fetch_user_feed
    def test_profile_edit_websites(self):
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_sites = {
            u'website': u'http://example.com/',
            u'twitter': u'http://twitter.com/lmorchard',
            u'github': u'http://github.com/lmorchard',
            u'stackoverflow': u'http://stackoverflow.com/users/lmorchard',
        }

        # Scrape out the existing significant form field values.
        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                   'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="%s"]' % fn).val()
        form['email'] = 'test@example.com'

        # Fill out the form with websites.
        form.update(dict(('websites_%s' % k, v)
                    for k, v in test_sites.items()))

        # Submit the form, verify redirect to profile detail
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        # Verify the websites are saved in the profile.
        eq_(test_sites, p.websites)

        # Verify the saved websites appear in the editing form
        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        for k, v in test_sites.items():
            eq_(v, doc.find('#profile-edit *[name="websites_%s"]' % k).val())

        # Come up with some bad sites, either invalid URL or bad URL prefix
        bad_sites = {
            u'website': u'HAHAHA WHAT IS A WEBSITE',
            u'twitter': u'http://facebook.com/lmorchard',
            u'stackoverflow': u'http://overqueueblah.com/users/lmorchard',
        }
        form.update(dict(('websites_%s' % k, v)
                    for k, v in bad_sites.items()))

        # Submit the form, verify errors for all of the bad sites
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-edit').length)
        tmpl = '#profile-edit #elsewhere .%s .errorlist'
        for n in ('website', 'twitter', 'stackoverflow'):
            eq_(1, doc.find(tmpl % n).length)

    @mock_put_mindtouch_user
    @mock_fetch_user_feed
    def test_profile_edit_interests(self):
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="%s"]' % fn).val()
        form['email'] = 'test@example.com'

        form['interests'] = ', '.join(test_tags)

        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        result_tags = [t.name.replace('profile:interest:', '')
                for t in p.tags.all_ns('profile:interest:')]
        result_tags.sort()
        test_tags.sort()
        eq_(test_tags, result_tags)

        test_expertise = ['css', 'canvas']
        form['expertise'] = ', '.join(test_expertise)
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        result_tags = [t.name.replace('profile:expertise:', '')
                for t in p.tags.all_ns('profile:expertise')]
        result_tags.sort()
        test_expertise.sort()
        eq_(test_expertise, result_tags)

        # Now, try some expertise tags not covered in interests
        test_expertise = ['css', 'canvas', 'mobile', 'movies']
        form['expertise'] = ', '.join(test_expertise)
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('.error #id_expertise').length)

    @mock_put_mindtouch_user
    @mock_fetch_user_feed
    def test_bug_709938_interests(self):
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_tags = [u'science,Technology,paradox,knowledge,modeling,big data,'
                     u'vector,meme,heuristics,harmony,mathesis universalis,'
                     u'symmetry,mathematics,computer graphics,field,chemistry,'
                     u'religion,astronomy,physics,biology,literature,'
                     u'spirituality,Art,Philosophy,Psychology,Business,Music,'
                     u'Computer Science']

        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="%s"]' % fn).val()
        form['email'] = 'test@example.com'

        form['interests'] = test_tags

        r = self.client.post(url, form, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, doc.find('ul.errorlist li').length)
        assert ('Ensure this value has at most 255 characters'
                in doc.find('ul.errorlist li').text())

    @mock_mindtouch_login
    @mock_get_deki_user
    @mock_put_mindtouch_user
    @mock_fetch_user_feed
    @mock.patch_object(Site.objects, 'get_current')
    def test_profile_edit_language_saves_to_mindtouch(self, get_current):
        get_current.return_value.domain = 'dev.mo.org'

        try:
            user = User.objects.get(username='testaccount')
            user.delete()
        except User.DoesNotExist:
            pass

        # log in as a MindTouch user to create django user & profile
        response = self.client.post(reverse('users.login', locale='en-US'),
                                    {'username': 'testaccount',
                                     'password': 'theplanet'}, follow=True)
        eq_(200, response.status_code)
        user = User.objects.get(username='testaccount')
        profile = UserProfile.objects.get(user=user)
        ok_(profile)

        # use profile edit to change language
        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code, 'Profile should be found.')
        doc = pq(r.content)

        # Scrape out the existing significant form field values.
        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                   'locale', 'timezone', 'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="%s"]' % fn).val()

        # Fill out the form with websites.
        form.update({'locale': 'nl'})
        form.update({'timezone': 'Europe/Amsterdam'})

        # Submit the form, verify redirect to profile detail
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        # Verify locale saved in the profile.
        eq_('nl', p.locale)

        # Verify the saved locale appears in the editing form
        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        ok_('nl', doc.find('#profile-edit select#id_locale option[value="nl"]'
                           '[selected="selected"]'))

        # TODO: Mock this part out...
        """
        r = requests.get(DekiUserBackend.profile_by_id_url % '=testaccount')
        doc = pq(r.content)
        eq_('nl', doc.find('language').text())
        """

    def _break(self, url, r):
        logging.debug("URL  %s" % url)
        logging.debug("STAT %s" % r.status_code)
        logging.debug("HEAD %s" % r.items())
        logging.debug("CONT %s" % r.content)
        ok_(False)


def get_datetime_from_string(string, string_format):
    new_datetime = datetime.datetime.fromtimestamp(time.mktime(
        time.strptime(string, string_format)))
    return new_datetime


def check_event_date(row):
    prev_end_datetime = datetime.datetime.today()
    datetime_format = "%Y-%m-%d"
    if (row.prev()):
        prev_datetime_str = row.prev().find('td').eq(1).text()
        prev_end_datetime = get_datetime_from_string(prev_datetime_str,
                                                     datetime_format)
    row_datetime_str = row.find('td').eq(1).text()
    row_datetime = get_datetime_from_string(row_datetime_str, datetime_format)
    logging.debug(row_datetime)
    logging.debug(prev_end_datetime)
    ok_(row_datetime < prev_end_datetime)


class EventsViewsTest(test_utils.TestCase):
    fixtures = ['devmo_calendar.json']

    def setUp(self):
        self.client = LocalizingClient()
        devmo_calendar_reload()

    def test_events(self):
        url = reverse('devmo.views.events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        # doc = pq(r.content)
        # past events ordered newest to oldest
        # rows = doc.find('table#past tr')
        # prev_end_datetime = datetime.datetime.today()
        # rows.each(check_event_date)


class SoapboxViewsTest(test_utils.TestCase):
    fixtures = ['devmo_calendar.json']

    def test_global_home(self):
        m = Message(message="Global", is_global=True, is_active=True, url="/")
        m.save()

        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

        url = reverse('events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

    def test_subsection(self):
        m = Message(message="Events", is_global=False, is_active=True,
                    url="/events/")
        m.save()

        url = reverse('events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_([], doc.find('div.global-notice'))

    def test_inactive(self):
        m = Message(message="Events", is_global=False, is_active=False,
                    url="/events/")
        m.save()

        url = reverse('events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_([], doc.find('div.global-notice'))
