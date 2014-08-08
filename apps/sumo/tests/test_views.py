from django.conf import settings

from nose.tools import eq_

from sumo.tests import TestCase


class RobotsTestCase(TestCase):
    # Use the hard-coded URL because it's well-known.
    old_setting = settings.ENGAGE_ROBOTS

    def tearDown(self):
        settings.ENGAGE_ROBOTS = self.old_setting

    def test_disengaged(self):
        settings.ENGAGE_ROBOTS = False
        response = self.client.get('/robots.txt')
        eq_('Disallow: /', response.content)
        eq_('text/plain', response['content-type'])

    def test_engaged(self):
        settings.ENGAGE_ROBOTS = True
        response = self.client.get('/robots.txt')
        eq_('text/plain', response['content-type'])
        assert len(response.content) > 11
