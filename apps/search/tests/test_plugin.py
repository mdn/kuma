# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.sites.models import Site

import mock
from nose.tools import eq_

from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class OpenSearchTestCase(TestCase):
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
