import os.path

from django.core.exceptions import ImproperlyConfigured

from constance.test import override_config
import mock
from googleapiclient.http import HttpMockSequence
from googleapiclient.errors import HttpError

from kuma.users.tests import UserTestCase

from . import revision
from ..utils import analytics_user_counts


GA_TEST_CREDS = r"""{
  "type": "service_account",
  "project_id": "test-suite-client",
  "private_key_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "private_key": "-----BEGIN PRIVATE KEY-----\n-----END PRIVATE KEY-----\n"
}
"""


class AnalyticsUserCountsTests(UserTestCase):
    @classmethod
    def setUpClass(cls):
        super(AnalyticsUserCountsTests, cls).setUpClass()

        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'analyticsreporting-discover.json')) as f:
            cls.valid_discovery = f.read()

    def setUp(self):
        self.rev1 = revision(save=True)
        self.rev2 = revision(save=True)

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS=GA_TEST_CREDS)
    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
    def test_successful_query(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        valid_response = """{"reports": [
            {
                "data": {
                    "rows": [
                        {
                            "metrics": [{"values": ["18775"]}],
                            "dimensions": ["%d"]
                        },
                        {
                            "metrics": [{"values": ["753"]}],
                            "dimensions": ["%d"]
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
        ]}""" % (self.rev1.id, self.rev2.id)

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, valid_response)
        ])

        results = analytics_user_counts([self.rev1, self.rev2])

        self.assertEqual(results, {self.rev1.id: 18775, self.rev2.id: 753})

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS=GA_TEST_CREDS)
    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
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

        results = analytics_user_counts([self.rev1])

        self.assertEqual(results, {self.rev1.id: 0})

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS=GA_TEST_CREDS)
    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
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
            analytics_user_counts([self.rev1, self.rev2])

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS=GA_TEST_CREDS)
    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
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
            analytics_user_counts([self.rev1, self.rev2])

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS=GA_TEST_CREDS)
    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
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
            analytics_user_counts([self.rev1, self.rev2])

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS="{}")
    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
    def test_credentials_not_configured(self, mock_credclass, mock_cache):
        # Mock the network traffic, just in case.
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '400'}, '')
        ])

        with self.assertRaises(ImproperlyConfigured):
            analytics_user_counts([self.rev1, self.rev2])

    @override_config(GOOGLE_ANALYTICS_CREDENTIALS="{'bad config']")
    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
    def test_credentials_malformed(self, mock_credclass, mock_cache):
        # Mock the network traffic, just in case.
        mock_cache.return_value = None

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '400'}, '')
        ])

        with self.assertRaises(ImproperlyConfigured):
            analytics_user_counts([self.rev1, self.rev2])
