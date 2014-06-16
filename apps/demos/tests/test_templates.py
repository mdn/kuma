from django.conf import settings

from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from kuma.users.tests import TestCaseBase


class SubmitTests(TestCaseBase):
    """Submit tests."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(SubmitTests, self).setUp()
        self.orig_debug = settings.DEBUG
        settings.DEBUG = True

    def tearDown(self):
        super(SubmitTests, self).tearDown()
        settings.DEBUG = self.orig_debug

    def test_derby_radio_buttons(self):
        '''Test derby radio buttons include a None option.'''
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('demos_submit'))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('challenge:none',
            doc.find('input#id_challenge_tags_0').attr('value'))
