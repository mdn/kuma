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
from waffle.models import Switch

from django.contrib.auth.models import User, AnonymousUser

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse


class LearnViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    def test_learn(self):
        url = reverse('landing.views.learn')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_html(self):
        url = reverse('landing.views.learn_html')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_css(self):
        url = reverse('landing.views.learn_css')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_javascript(self):
        url = reverse('landing.views.learn_javascript')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)


class LandingViewsTest(test_utils.TestCase):
    fixtures = ['test_data.json', ]

    def setUp(self):
        self.client = LocalizingClient()

    def test_home(self):
        url = reverse('landing.views.home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        dev_mdc_link = doc.find('a#dev-mdc-link')
        ok_(dev_mdc_link)

    def test_addons(self):
        url = reverse('landing.views.addons')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_mozilla(self):
        url = reverse('landing.views.mozilla')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_mobile(self):
        url = reverse('landing.views.mobile')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_web(self):
        url = reverse('landing.views.web')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_search(self):
        url = reverse('landing.views.search')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_promote_buttons(self):
        url = reverse('landing.views.promote_buttons')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_discussion(self):
        url = reverse('landing.views.discussion')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_discussion_archive_link_waffled(self):
        url = reverse('landing.views.discussion')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        phpbb_link = doc.find('a#forum-archive-link')
        eq_('/forums', phpbb_link.attr('href'))

        s = Switch.objects.create(name='static_forums', active=True)
        s.save()
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        phpbb_link = doc.find('a#forum-archive-link')
        eq_('/forum-archive/', phpbb_link.attr('href'))

    def test_forum_archive(self):
        url = reverse('landing.views.forum_archive')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
