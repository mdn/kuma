import logging
import csv
import shlex
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
from devmo.models import Calendar, Event, UserProfile

from dekicompat.backends import DekiUser

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse


def parse_robots(base_url):
    """ Given a base url, retrieves the robot.txt file and
        returns a list of rules. A rule is a tuple.
        Example:
        [("User-Agent", "*"), ("Crawl-delay", "5"),
         ...
         ("Disallow", "/template")]

        Tokenizes input to whitespace won't break
        these acceptance tests.
    """
    rules = []
    robots = shlex.shlex(urllib2.urlopen("%s/robots.txt" % base_url))
    robots.whitespace_split = True
    token = robots.get_token()
    while token:
        rule = None
        if token[-1] == ':':
            rule = (token[0:-1], robots.get_token())
        if rule:
            rules.append(rule)
        token = robots.get_token()
    return rules


class TestDevMoRobots(test_utils.TestCase):
    """ These are really acceptance tests, but we seem to lump
        together unit, integration, regression, and
        acceptance tests """
    def test_production(self):
        rules = [
            ("User-Agent", "*"),
            ("Crawl-delay", "5"),
            ("Sitemap", "sitemap.xml"),
            ("Request-rate", "1/5"),
            ("Disallow", "/@api/deki/*"),
            ("Disallow", "/*feed=rss"),
            ("Disallow", "/*type=feed"),
            ("Disallow", "/skins"),
            ("Disallow", "/template:"),
        ]
        eq_(parse_robots('http://developer.mozilla.org'),  rules)
        eq_(parse_robots('https://developer.mozilla.org'), rules)

    def test_stage_bug607996(self):
        rules = [
            ("User-agent", "*"),
            ("Disallow", "/"),
        ]

        #No https://mdn.staging.mozilla.com, this serves up Sumo
        eq_(parse_robots('http://mdn.staging.mozilla.com'), rules)

        eq_(parse_robots('https://developer-stage.mozilla.org'), rules)
        eq_(parse_robots('http://developer-stage.mozilla.org'),  rules)

        eq_(parse_robots('https://developer-stage9.mozilla.org'), rules)
        eq_(parse_robots('http://developer-stage9.mozilla.org'),  rules)


class TestDevMoHelpers(test_utils.TestCase):
    def test_devmo_url(self):
        en_only_page = '/en/HTML/HTML5'
        localized_page = '/en/HTML'
        req = test_utils.RequestFactory().get('/')
        context = {'request': req}

        req.locale = 'en-US'
        eq_(devmo_url(context, en_only_page), en_only_page)
        req.locale = 'de'
        eq_(devmo_url(context, localized_page), '/de/HTML')
        req.locale = 'zh-TW'
        eq_(devmo_url(context, localized_page), '/zh_tw/HTML')


class TestDevMoUrlResolvers(test_utils.TestCase):
    def test_prefixer_get_language(self):
        # language precedence is GET param > cookie > Accept-Language
        req = test_utils.RequestFactory().get('/', {'lang': 'es'})
        prefixer = urlresolvers.Prefixer(req)
        eq_(prefixer.get_language(), 'es')

        req = test_utils.RequestFactory().get('/')
        req.COOKIES['lang'] = 'de'
        prefixer = urlresolvers.Prefixer(req)
        eq_(prefixer.get_language(), 'de')

        req = test_utils.RequestFactory().get('/')
        req.META['HTTP_ACCEPT_LANGUAGE'] = 'fr'
        prefixer = urlresolvers.Prefixer(req)
        eq_(prefixer.get_language(), 'fr')


APP_DIR = dirname(__file__)
MOZILLA_PEOPLE_EVENTS_CSV = '%s/fixtures/Mozillapeopleevents.csv' % APP_DIR
XSS_CSV = '%s/fixtures/xss.csv' % APP_DIR
BAD_DATE_CSV = '%s/fixtures/bad_date.csv' % APP_DIR


class TestCalendar(test_utils.TestCase):

    def setUp(self):
        self.cal = Calendar.objects.get(shortname='devengage_events')
        self.event = Event(date="2011-06-17", conference="Web2Day",
                           location="Nantes, France",
                           people="Christian Heilmann",
                           description="TBD", done="no", calendar=self.cal)
        self.event.save()

    def test_reload_bad_url_does_not_delete_data(self):
        self.cal.url = 'bad'
        success = self.cal.reload()
        ok_(success == False)
        ok_(Event.objects.all()[0].conference == 'Web2Day')
        self.cal.url = 'http://test.com/testcalspreadsheet'
        success = self.cal.reload()
        ok_(success == False)
        ok_(Event.objects.all()[0].conference == 'Web2Day')

    def test_reload_from_csv_data(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # check total
        assert_equal(33, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_reload_from_csv_data_blank_end_date(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # check total
        assert_equal(33, len(Event.objects.all()))
        # spot-check
        event = Event.objects.get(conference='Monash University')
        ok_(event)
        eq_(None, event.end_date)

    def test_bad_date_column_skips_row(self):
        self.cal.reload(data=csv.reader(open(BAD_DATE_CSV, 'rb')))
        # check total - should still have the good row
        assert_equal(1, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_html_santiziation(self):
        self.cal.reload(data=csv.reader(open(XSS_CSV, 'rb')))
        # spot-check
        eq_('&lt;script&gt;alert("ruh-roh");&lt;/script&gt;Brendan Eich',
            Event.objects.get(conference="Texas JavaScript").people)


class CalendarViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    def test_events(self):
        url = reverse('events')
        r = self.client.get(url)
        d = pq(r.content)
        eq_(200, r.status_code)
        eq_("Where is Mozilla?", d('h1.page-title').text())


class ProfileViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    @attr('profile')
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    @patch('dekicompat.backends.DekiUserBackend.get_deki_user')
    def test_profile_view(self, authenticate, get_user, get_deki_user):
        """A user profile can be viewed"""
        (user, deki_user, profile) = self._create_profile()
        authenticate.return_value = user
        get_user.return_value = user
        # TODO: Why does this break things?
        #get_deki_user.return_value = deki_user

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
        eq_(profile.bio,
            doc.find('#profile-head.vcard .bio').text())

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
        profile.bio = "I am a freaky space alien."
        profile.save()

        return (user, deki_user, profile)

    @attr('profile_edit')
    @patch('dekicompat.backends.DekiUserBackend.authenticate')
    @patch('dekicompat.backends.DekiUserBackend.get_user')
    @patch('dekicompat.backends.DekiUserBackend.get_deki_user')
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

    def _break(self, url, r):
        logging.debug("URL  %s" % url)
        logging.debug("STAT %s" % r.status_code)
        logging.debug("HEAD %s" % r.items())
        logging.debug("CONT %s" % r.content)
        ok_(False)
