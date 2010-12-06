from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class TwitterMiddlewareTests(TestCase):
    """Tests for the Twitter auth middleware."""

    def test_logout(self):
        """Ensure logout POST request works."""
        landing_url = reverse('customercare.landing', locale='en-US')
        resp = self.client.post(landing_url, {'twitter_delete_auth': 1})
        self.assertRedirects(resp, landing_url)
