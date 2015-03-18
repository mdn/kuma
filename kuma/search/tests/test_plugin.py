from __future__ import absolute_import
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_

from kuma.core.tests import KumaTestCase
from kuma.core.urlresolvers import reverse


class OpenSearchTestCase(KumaTestCase):
    """Test the Kuma OpenSearch plugin."""

    @mock.patch.object(Site.objects, 'get_current')
    def test_plugin(self, get_current):
        """The plugin loads with the correct mimetype."""
        get_current.return_value.domain = 'testserver'

        response = self.client.get(reverse('search.plugin',
                                           locale='en-US'))
        eq_(200, response.status_code)
        assert 'expires' in response
        eq_('application/opensearchdescription+xml', response['content-type'])

    @mock.patch.object(Site.objects, 'get_current')
    def test_localized_plugin(self, get_current):
        """Every locale gets its own plugin!"""
        get_current.return_value.domain = 'testserver'

        response = self.client.get(reverse('search.plugin',
                                           locale='en-US'))
        assert '/en-US/search' in response.content

        response = self.client.get(reverse('search.plugin',
                                           locale='fr'))
        assert '/fr/search' in response.content
