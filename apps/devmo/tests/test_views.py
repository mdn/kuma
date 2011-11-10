import datetime
import logging
import csv
import shlex
import time
import urllib2
from os.path import basename, dirname, isfile, isdir

from mock import patch
from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
import test_utils

from django.contrib.auth.models import User, AnonymousUser

from devmo.helpers import devmo_url
from devmo import urlresolvers
from devmo.models import Calendar, Event, UserProfile, UserDocsActivityFeed
from devmo.forms import UserProfileEditForm
from devmo.cron import devmo_calendar_reload

from dekicompat.backends import DekiUser

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse


APP_DIR = dirname(dirname(__file__))
USER_DOCS_ACTIVITY_FEED_XML = ('%s/fixtures/user_docs_activity_feed.xml' %
                               APP_DIR)


class ProfileViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    @attr('docs_activity')
    @patch('devmo.models.UserDocsActivityFeed.fetch_user_feed')
    @patch('dekicompat.backends.DekiUserBackend.get_deki_user')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    def test_profile_view(self, authenticate, get_user, get_deki_user,
                          fetch_user_feed):
        """A user profile can be viewed"""
        (user, deki_user, profile) = self._create_profile()
        authenticate.return_value = user
        get_user.return_value = user
        # TODO: Why does this break things?
        #get_deki_user.return_value = deki_user
        doc_feed_data = open(USER_DOCS_ACTIVITY_FEED_XML, 'r').read()
        fetch_user_feed.return_value = doc_feed_data

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

    @attr('current')
    @patch('devmo.models.UserDocsActivityFeed.fetch_user_feed')
    @patch('dekicompat.backends.DekiUserBackend.get_deki_user')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    def test_bug_698971(self, authenticate, get_user, get_deki_user,
                        fetch_user_feed):
        """A non-numeric page number should not cause an error"""
        (user, deki_user, profile) = self._create_profile()

        authenticate.return_value = user
        get_user.return_value = user
        doc_feed_data = open(USER_DOCS_ACTIVITY_FEED_XML, 'r').read()
        fetch_user_feed.return_value = doc_feed_data
        
        url = '%s?page=asdf' % reverse('devmo.views.profile_view',
                                       args=(user.username,))

        try:
            r = self.client.get(url, follow=True)
        except PageNotAnInteger:
            ok_(False, "Non-numeric page number should not cause an error")

    @patch('dekicompat.backends.DekiUserBackend.get_deki_user')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    def test_profile_edit(self, authenticate, get_user, get_deki_user):
        (user, deki_user, profile) = self._create_profile()

        authenticate.return_value = user
        get_user.return_value = user
        # TODO: Why does this break things?
        #get_deki_user.return_value = deki_user

        url = reverse('devmo.views.profile_view',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(0, doc.find('#profile-head .edit .button').length)

        self.client.cookies['authtoken'] = 'qwertyuiop'

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

    @attr("edit_websites")
    @patch('dekicompat.backends.DekiUserBackend.get_deki_user')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    def test_profile_edit_websites(self, authenticate, get_user,
                                   get_deki_user):
        (user, deki_user, profile) = self._create_profile()

        authenticate.return_value = user
        get_user.return_value = user
        # TODO: Why does this break things?
        #get_deki_user.return_value = deki_user

        self.client.cookies['authtoken'] = 'qwertyuiop'

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

    @attr("edit_interests")
    @patch('dekicompat.backends.DekiUserBackend.get_deki_user')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    def test_profile_edit_tags(self, authenticate, get_user,
                                   get_deki_user):
        (user, deki_user, profile) = self._create_profile()

        authenticate.return_value = user
        get_user.return_value = user

        self.client.cookies['authtoken'] = 'qwertyuiop'

        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="%s"]' % fn).val()

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

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

    def _create_profile(self):
        """Create a user, deki_user, and a profile for a test account"""
        user = User.objects.create_user('tester23', 'tester23@example.com',
                                        'trustno1')

        deki_user = DekiUser(id=0, username='tester23',
                             fullname='Tester Twentythree',
                             email='tester23@example.com',
                             gravatar='', profile_url=None)

        profile = UserProfile()
        profile.user = user
        profile.fullname = "Tester Twentythree"
        profile.title = "Spaceship Pilot"
        profile.organization = "UFO"
        profile.location = "Outer Space"
        profile.irc_nickname = "ircuser"
        profile.bio = "I am a freaky space alien."
        profile.save()

        return (user, deki_user, profile)

    def _break(self, url, r):
        logging.debug("URL  %s" % url)
        logging.debug("STAT %s" % r.status_code)
        logging.debug("HEAD %s" % r.items())
        logging.debug("CONT %s" % r.content)
        ok_(False)

def get_datetime_from_string(string, string_format):
    new_datetime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(string, string_format)))
    return new_datetime

def check_event_date(row):
    prev_end_datetime = datetime.datetime.today()
    datetime_format = "%Y-%m-%d"
    if (row.prev()):
        prev_datetime_str = row.prev().find('td').eq(1).text()
        prev_end_datetime = get_datetime_from_string(prev_datetime_str, datetime_format)
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
        doc = pq(r.content)

        # past events ordered newest to oldest
        # rows = doc.find('table#past tr')
        # prev_end_datetime = datetime.datetime.today()
        # rows.each(check_event_date)
