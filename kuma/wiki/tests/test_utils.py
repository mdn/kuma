from __future__ import unicode_literals

import datetime
import os.path


import mock
import pytest
from constance.test import override_config
from django.core.exceptions import ImproperlyConfigured
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMockSequence

from kuma.core.tests import KumaTestCase
from kuma.users.tests import UserTestCase

from . import revision
from ..exceptions import NotDocumentView
from ..utils import analytics_upageviews, analytics_upageviews_by_revisions, get_doc_components_from_url


GA_TEST_CREDS = r"""{
  "type": "service_account",
  "project_id": "test-suite-client",
  "private_key_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "private_key": "-----BEGIN PRIVATE KEY-----\n-----END PRIVATE KEY-----\n"
}
"""


class RecordingHttpMockSequence(HttpMockSequence):
    def __init__(self, iterable):
        super(RecordingHttpMockSequence, self).__init__(iterable)
        self.request_calls = []

    def request(self, *args, **kwargs):
        self.request_calls.append((args, kwargs))
        return super(RecordingHttpMockSequence, self).request(*args, **kwargs)


@override_config(GOOGLE_ANALYTICS_CREDENTIALS=GA_TEST_CREDS)
@mock.patch('googleapiclient.discovery_cache.autodetect')
@mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
class AnalyticsUpageviewsTests(KumaTestCase):
    start_date = datetime.date(2016, 1, 1)
    valid_response = b"""{"reports": [
            {
                "data": {
                    "rows": [
                        {
                            "metrics": [{"values": ["18775"]}],
                            "dimensions": ["1068728"]
                        },
                        {
                            "metrics": [{"values": ["753"]}],
                            "dimensions": ["1074760"]
                        }
                    ],
                    "maximums": [{"values": ["18775"]}],
                    "minimums": [{"values": ["753"]}],
                    "samplingSpaceSizes": ["2085651"],
                    "totals": [{"values": ["19528"]}],
                    "rowCount": 2,
                    "samplesReadCounts": ["999997"]
                },
                "columnHeader": {
                    "dimensions": ["ga:dimension12"],
                    "metricHeader": {
                        "metricHeaderEntries": [
                            {"type": "INTEGER", "name": "ga:uniquePageviews"}
                        ]
                    }
                }
            }
        ]}"""

    @classmethod
    def setUpClass(cls):
        super(AnalyticsUpageviewsTests, cls).setUpClass()

        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'analyticsreporting-discover.json')) as f:
            cls.valid_discovery = f.read()

    def test_successful_query(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, self.valid_response)
        ])

        results = analytics_upageviews([1068728, 1074760], self.start_date)

        self.assertEqual(results, {1068728: 18775, 1074760: 753})

    def test_datetime_instead_of_date(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        sequence = RecordingHttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, self.valid_response)
        ])
        mock_creds.authorize.return_value = sequence

        start_date = datetime.datetime(2016, 1, 31, 17, 32)
        results = analytics_upageviews([1068728, 1074760], start_date)

        # Check that the last request's parameters contain a
        # representation of the start date, not the starting datetime.
        args, kwargs = sequence.request_calls[-1]
        self.assertIn('"startDate": "2016-01-31"', kwargs['body'])

        self.assertEqual(results, {1068728: 18775, 1074760: 753})

    def test_end_date(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        sequence = RecordingHttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, self.valid_response)
        ])
        mock_creds.authorize.return_value = sequence

        end_date = datetime.date(2016, 1, 31)
        results = analytics_upageviews([1068728, 1074760], self.start_date, end_date)

        # Check that the last request's parameters contain a
        # representation of the end date, not the ending datetime.
        args, kwargs = sequence.request_calls[-1]
        self.assertIn('"endDate": "2016-01-31"', kwargs['body'])

        self.assertEqual(results, {1068728: 18775, 1074760: 753})

    def test_end_date_datetime_instead_of_date(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        sequence = RecordingHttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, self.valid_response)
        ])
        mock_creds.authorize.return_value = sequence

        end_date = datetime.datetime(2016, 1, 31, 17, 32)
        results = analytics_upageviews([1068728, 1074760], self.start_date, end_date)

        # Check that the last request's parameters contain a
        # representation of the end date, not the ending datetime.
        args, kwargs = sequence.request_calls[-1]
        self.assertIn('"endDate": "2016-01-31"', kwargs['body'])

        self.assertEqual(results, {1068728: 18775, 1074760: 753})

    def test_longs_instead_of_ints(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        sequence = RecordingHttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, self.valid_response)
        ])
        mock_creds.authorize.return_value = sequence

        results = analytics_upageviews([1068728, 1074760], self.start_date)

        args, kwargs = sequence.request_calls[-1]
        self.assertIn('["1068728", "1074760"]', kwargs['body'])

        self.assertEqual(results, {1068728: 18775, 1074760: 753})

    def test_unmatching_query(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        # This is the type of data we get back if the rev doesn't match anything.
        empty_response = """{"reports": [
            {
                "data": {
                    "samplingSpaceSizes": ["2085651"],
                    "totals": [{"values": ["0"]}],
                    "samplesReadCounts": ["999997"]
                },
                "columnHeader": {
                    "dimensions": ["ga:dimension12"],
                    "metricHeader": {
                        "metricHeaderEntries": [
                            {"type": "INTEGER", "name": "ga:uniquePageviews"}
                        ]
                    }
                }
            }
        ]}"""

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, empty_response)
        ])

        results = analytics_upageviews([42], self.start_date)

        self.assertEqual(results, {42: 0})

    def test_invalid_viewid(self, mock_credclass, mock_cache):
        # http 400

        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '400'}, '')
        ])

        with self.assertRaises(HttpError):
            analytics_upageviews([1068728, 1074760], self.start_date)

    def test_failed_authentication(self, mock_credclass, mock_cache):
        # http 401

        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '401'}, '')
        ])

        with self.assertRaises(HttpError):
            analytics_upageviews([1068728, 1074760], self.start_date)

    def test_user_does_not_have_analytics_account(self, mock_credclass, mock_cache):
        # http 403

        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '403'}, '')
        ])

        with self.assertRaises(HttpError):
            analytics_upageviews([1068728, 1074760], self.start_date)

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS="{}")
    def test_credentials_not_configured(self, mock_credclass, mock_cache):
        # Mock the network traffic, just in case.
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '400'}, '')
        ])

        with self.assertRaises(ImproperlyConfigured):
            analytics_upageviews([1068728, 1074760], self.start_date)

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS="{'bad config']")
    def test_credentials_malformed(self, mock_credclass, mock_cache):
        # Mock the network traffic, just in case.
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '400'}, '')
        ])

        with self.assertRaises(ImproperlyConfigured):
            analytics_upageviews([1068728, 1074760], self.start_date)


@mock.patch('kuma.wiki.utils.analytics_upageviews')
class AnalyticsUpageviewsByRevisionsTests(UserTestCase):
    def setUp(self):
        self.rev1 = revision(save=True)
        self.rev2 = revision(save=True)

    def test_empty_call(self, mock_pageviews):
        results = analytics_upageviews_by_revisions([])

        self.assertEqual(results, {})
        self.assertFalse(mock_pageviews.called)

    def test_success(self, mock_pageviews):
        analytics_upageviews_by_revisions([self.rev1, self.rev2])

        mock_pageviews.assert_called_once_with([self.rev1.id, self.rev2.id],
                                               min(self.rev1.created, self.rev2.created))


def test_get_doc_components_from_url_absolute_url(root_doc):
    """get_doc_components_from_url works with an absolute URL (path)."""
    url = root_doc.get_absolute_url()
    locale, path, slug = get_doc_components_from_url(url)
    assert locale == root_doc.locale
    assert path == '/docs/Root'
    assert slug == root_doc.slug


def test_get_doc_components_from_url_wrong_required_locale(root_doc):
    """get_doc_components_from_url returns False for wrong required_locale."""
    url = root_doc.get_absolute_url()
    assert root_doc.locale != 'de'
    components = get_doc_components_from_url(url, required_locale='de')
    assert components is False


def test_get_doc_components_from_url_correct_required_locale(root_doc):
    """get_doc_components_from_url works for correct required_locale."""
    url = root_doc.get_absolute_url()
    locale, path, slug = get_doc_components_from_url(
        url, required_locale=root_doc.locale)
    assert locale == root_doc.locale
    assert path == '/docs/Root'
    assert slug == root_doc.slug


def test_get_doc_components_from_url_check_host_same_domain(root_doc):
    """get_doc_components_from_url works with check_host and full local URL."""
    url = root_doc.get_full_url()
    locale, path, slug = get_doc_components_from_url(url, check_host=True)
    assert locale == root_doc.locale
    assert path == '/docs/Root'
    assert slug == root_doc.slug


def test_get_doc_components_from_url_check_host_diff_domain(root_doc):
    """get_doc_components_from_url fails on check_host with remote URL."""
    url = 'http://example.com' + root_doc.get_absolute_url()
    components = get_doc_components_from_url(url, check_host=True)
    assert components is False


def test_get_doc_components_from_url_raises_on_non_doc_url(create_revision):
    """get_doc_components_from_url raises on a non-document URL."""
    url = create_revision.get_absolute_url()
    with pytest.raises(NotDocumentView):
        get_doc_components_from_url(url)
