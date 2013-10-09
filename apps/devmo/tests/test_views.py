import datetime
import logging
import time
from os.path import dirname

import requests

import mock
from mock import patch
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
import test_utils
from devmo.tests import create_profile

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.paginator import PageNotAnInteger

from soapbox.models import Message

from devmo.models import UserProfile

from devmo.cron import devmo_calendar_reload

from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse

from waffle.models import Flag

TESTUSER_PASSWORD = 'testpass'


class ProfileViewsTest(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client = LocalizingClient()
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    def _get_current_form_field_values(self, doc):
        # Scrape out the existing significant form field values.
        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                   'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="%s"]' % fn).val()
        return form

    @attr('docs_activity')
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

    def test_my_profile_view(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get('/profile/')
        eq_(302, resp.status_code)
        ok_(reverse('devmo.views.profile_view', args=(u.username,)) in
            resp['Location'])

    def test_bug_698971(self):
        """A non-numeric page number should not cause an error"""
        (user, profile) = create_profile()

        url = '%s?page=asdf' % reverse('devmo.views.profile_view',
                                       args=(user.username,))

        try:
            self.client.get(url, follow=True)
        except PageNotAnInteger:
            ok_(False, "Non-numeric page number should not cause an error")

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

        edit_button = doc.find('#profile-head .edit #edit-profile')
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
            email='testuser@test.com',
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

    def test_my_profile_edit(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get('/profile/edit')
        eq_(302, resp.status_code)
        ok_(reverse('devmo.views.profile_edit', args=(u.username,)) in
            resp['Location'])

    def test_profile_edit_beta(self):
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(None, doc.find('input#id_beta').attr('checked'))

        form = self._get_current_form_field_values(doc)
        form['beta'] = True

        r = self.client.post(url, form, follow=True)

        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_('checked', doc.find('input#id_beta').attr('checked'))

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
            u'linkedin': u'https://www.linkedin.com/in/testuser',
            u'mozillians': u'https://mozillians.org/u/testuser',
            u'facebook': u'https://www.facebook.com/test.user'
        }

        form = self._get_current_form_field_values(doc)

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

    def test_profile_edit_interests(self):
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('devmo.views.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

        form = self._get_current_form_field_values(doc)

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

        form = self._get_current_form_field_values(doc)

        form['interests'] = test_tags

        r = self.client.post(url, form, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, doc.find('ul.errorlist li').length)
        assert ('Ensure this value has at most 255 characters'
                in doc.find('ul.errorlist li').text())


    def test_bug_698126_l10n(self):
        """Test that the form field names are localized"""
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
            password=TESTUSER_PASSWORD)

        url = reverse('devmo.views.profile_edit',
            args=(user.username,))
        r = self.client.get(url, follow=True)
        for field in r.context['form'].fields:
            # if label is localized it's a lazy proxy object
            ok_(not isinstance(
                r.context['form'].fields[field].label, basestring),
                'Field %s is a string!' % field)

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

    def test_events_map_flag(self):
        url = reverse('devmo.views.events')

        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_([], doc.find('#map_canvas'))
        ok_("maps.google.com" not in r.content)

        events_map_flag = Flag.objects.create(name='events_map', everyone=True)
        events_map_flag.save()

        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, len(doc.find('#map_canvas')))
        ok_("maps.google.com" in r.content)

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

class LoggingTests(test_utils.TestCase):
    urls = 'devmo.tests.logging_urls'

    def setUp(self):
        self.old_logging = settings.LOGGING

    def tearDown(self):
        settings.LOGGING = self.old_logging

    def test_no_mail_handler(self):
        try:
            response = self.client.get('/en-US/test_exception/')
            eq_(500, response.status_code)
            eq_(0, len(mail.outbox))
        except:
            pass

    def test_mail_handler(self):
        settings.LOGGING['loggers']['django.request'] = ['console', 'mail_admins']
        try:
            response = self.client.get('/en-US/test_exception/')
            eq_(500, response.status_code)
            eq_(1, len(mail.outbox))
        except:
            pass
