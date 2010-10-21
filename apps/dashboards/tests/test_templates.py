from nose.tools import eq_

from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class LocalizationDashTests(TestCase):
    def test_render(self):
        """Assert the main dash renders and doesn't crash."""
        response = self.client.get(reverse('dashboards.localization',
                                           locale='de'),
                                   follow=False)
        eq_(200, response.status_code)

    def test_untranslated_detail(self):
        """Assert the whole-page Untranslated Articles view works."""
        # We shouldn't have to write tests for every whole-page view: just
        # enough to cover all the different kinds of table templates.
        response = self.client.get(reverse('dashboards.localization_detail',
                                           args=['untranslated'],
                                           locale='de'))
        eq_(200, response.status_code)
