from __future__ import absolute_import
from django.contrib.sites.models import Site

import mock
import test_utils
from nose.tools import eq_

from sumo.urlresolvers import reverse


class OpenSearchTestCase(test_utils.TestCase):
    """Test the SUMO OpenSearch plugin."""

    @mock.patch_object(Site.objects, 'get_current')
    def test_plugin(self, get_current):
        """The plugin loads with the correct mimetype."""
        get_current.return_value.domain = 'testserver'

        response = self.client.get(reverse('search.plugin',
                                           locale='en-US'))
        eq_(200, response.status_code)
        assert 'expires' in response
        eq_('application/opensearchdescription+xml', response['content-type'])

    @mock.patch_object(Site.objects, 'get_current')
    def test_localized_plugin(self, get_current):
        """Every locale gets its own plugin!"""
        get_current.return_value.domain = 'testserver'

        response = self.client.get(reverse('search.plugin',
                                           locale='en-US'))
        assert '/en-US/search' in response.content

        response = self.client.get(reverse('search.plugin',
                                           locale='fr'))
        assert '/fr/search' in response.content
