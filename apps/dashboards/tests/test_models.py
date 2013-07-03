# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf import settings

from mock import patch_object
from nose.tools import raises, eq_

from dashboards.models import (WikiDocumentVisits, StatsException, THIS_WEEK,
                               StatsIOError)
from devmo.tests import SkippedTestCase
from wiki.tests import document, revision


class DocumentVisitsTests(SkippedTestCase):
    """Tests for the WebTrends statistics gathering"""
    fixtures = ['test_users.json']

    @raises(StatsException)
    def test_bad_json(self):
        """Raise a nice error if WebTrends hands us bad JSON."""
        WikiDocumentVisits._visit_counts('{')

    @raises(StatsException)
    def test_no_data_attr(self):
        """Raise a nice err if WebTrends returns an obj with no 'data' attr."""
        WikiDocumentVisits._visit_counts('{}')

    @raises(StatsException)
    def test_not_subscriptable(self):
        """Raise a nice err if WebTrends returns an unsubscriptable obj."""
        WikiDocumentVisits._visit_counts('8')

    def test_no_pages(self):
        """Don't pave over current data if WebTrends returns well-formatted
        data structure with no interesting data in it."""
        # Get some JSON that contains no interesting data.
        no_pages = '{"data": {"12/01/2010-12/07/2010": {"SubRows": {}}}}'
        counts = WikiDocumentVisits._visit_counts(no_pages)
        eq_({}, counts)  # Make sure nothing interesting is there.

        # Try to reload visits table from the uninteresting data:
        d = document()
        d.save()
        v = WikiDocumentVisits.objects.create(document=d, visits=12,
                                              period=THIS_WEEK)
        WikiDocumentVisits.reload_period_from_json(THIS_WEEK, no_pages)

        # Visits table should remain unchanged:
        eq_(1, WikiDocumentVisits.objects.filter(pk=v.pk).count())

    def test_no_locale(self):
        """Skip URLs with no locale."""
        eq_({}, WikiDocumentVisits._visit_counts('{"data": {"12/01/2010-12/07/'
            '2010": {"SubRows":{"http://support.mozilla.com/home":8}}}}'))

    def test_foreign_locale(self):
        """Skip URLs with non-English locale."""
        eq_({}, WikiDocumentVisits._visit_counts('{"data": {"12/01/2010-12/07/'
            '2010": {"SubRows":{"http://support.mozilla.com/zh/home/":8}}}}'))

    def test_unknown_view(self):
        """Skip URLs that don't resolve."""
        eq_({}, WikiDocumentVisits._visit_counts('{"data": {"12/01/2010-12/07/'
            '2010": {"SubRows":{"http://support.mozilla.com/%s/unknown/":8}}}}'
            % settings.LANGUAGE_CODE))

    def test_non_document_view(self):
        """Skip URLs that don't resolve to the wiki document view."""
        eq_({}, WikiDocumentVisits._visit_counts('{"data": {"12/01/2010-12/07/'
            '2010": {"SubRows":{"http://support.mozilla.com/%s/contributors":8'
            '}}}}' % settings.LANGUAGE_CODE))

    def test_bad_visit_count(self):
        """Skip URLs whose visit counts aren't ints."""
        d = revision(is_approved=True, save=True).document
        eq_({}, WikiDocumentVisits._visit_counts('{"data": {"12/01/2010-12/07/'
            '2010": {"SubRows":{"http://support.mozilla.com/%s/kb/%s":{'
            '"measures":{"Visits":"non-integer"}}}}}}'
            % (settings.LANGUAGE_CODE, d.slug)))

    def test_bad_page_info(self):
        """Skip URLs whose page info is unsubscriptable."""
        d = revision(is_approved=True, save=True).document
        eq_({}, WikiDocumentVisits._visit_counts('{"data": {"12/01/2010-12/07/'
            '2010": {"SubRows":{"http://support.mozilla.com/%s/kb/%s":8}}}}'
            % (settings.LANGUAGE_CODE, d.slug)))

    def test_good_visit_count(self):
        """Extract visit counts from good data.

        It has some nasty non-ASCII chars in it.

        """
        d = revision(document=document(slug='hellỗ', save=True),
                     is_approved=True, save=True).document
        d2 = revision(document=document(slug='there', save=True),
                      is_approved=True, save=True).document
        # We get a str, not a unicode obj, out of the urllib call.
        eq_({d.pk: 1037639, d2.pk: 213817}, WikiDocumentVisits._visit_counts(
            '{"data": {"12/01/2010-12/07/2010": {"SubRows":{'
            '"http://support.mozilla.com/%s/kb/hellỗ":{"Attributes":{"Title":'
            '"Firefox Support Home Page | Firefox Support","UrlLink":'
            '"http://support.mozilla.com/en-US/home/"},"measures":'
            '{"Visits":1037639.0,"Views":3357731.0,"Average Time Viewed":23.0'
            '},"SubRows":null},"http://support.mozilla.com/%s/kb/there":'
            '{"Attributes":{"Title":"Startseite der Firefox-Hilfe | Firefox'
            'Support","UrlLink":"http://support.mozilla.com/de/home/"},'
            '"measures":{"Visits":213817.0,"Views":595329.0,"Average Time '
            'Viewed":25.0},"SubRows":null}}}}}'
            % ((settings.LANGUAGE_CODE,) * 2)))
