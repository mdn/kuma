import json
import logging

from django.conf import settings

from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from wiki.models import VersionMetadata, Document, Revision
from wiki.tests import doc_rev, document, new_document_data, revision
from wiki.views import _version_groups

class DocsLandingNeedsReviewTests(TestCase):

    fixtures = ['test_users.json']

    def test_review_tags(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        data = new_document_data()
        data.update({'review_tags':['editorial']})
        response = client.post(reverse('wiki.new_document'), data)

        doc = Document.objects.get(slug="a-test-article")

        combos = (
            ([], 0, 0, 0, 0),
            (['technical',], 1, 1, 0, 0),
            (['editorial',], 0, 0, 1, 1),
            (['technical', 'editorial',], 1, 1, 1, 1),
        )

        for tags, a, b, c, d in combos:

            # Edit the page and set the tags for this test
            data.update({ 'form': 'rev', 'review_tags': tags })
            response = client.post(reverse('wiki.edit_document', args=[doc.slug]), data)

            response = client.get(reverse('docs.views.docs'))
            page = pq(response.content)

            # Check for the section itself, and then the doc 
            eq_(a, page('div#review-technical').length)
            eq_(b, page("div#review-technical ul li h4 a:contains('%s')" %
                doc.title).length)
            eq_(c, page('div#review-editorial').length)
            eq_(d, page("div#review-editorial ul li h4 a:contains('%s')" %
                doc.title).length)

