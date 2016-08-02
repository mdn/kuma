import os.path

import mock
from googleapiclient.http import HttpMockSequence
from googleapiclient.errors import HttpError
from kuma.core.tests import KumaTestCase

from ..utils import analytics_user_counts


class AnalyticsUserCountsTests(KumaTestCase):
    def setUp(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'analyticsreporting-discover.json')) as f:
            self.valid_discovery = f.read()

    @mock.patch('googleapiclient.discovery_cache.autodetect')
    @mock.patch('kuma.wiki.utils.ServiceAccountCredentials')
    def test_successful_query(self, mock_credclass, mock_cache):
        # Disable the discovery cache, so that we can fully control the http requests
        # with HttpMockSequence below
        mock_cache.return_value = None

        valid_response = """{"reports": [
            {
                "data": {
                    "rowCount": 2,
                    "rows": [
                        {
                            "metrics": [{"values": ["15113"]}],
                            "dimensions": ["1068728"]
                        },
                        {
                            "metrics": [{"values": ["847"]}],
                            "dimensions": ["1074760"]
                        }
                    ],
                    "maximums": [{"values": ["15113"]}],
                    "minimums": [{"values": ["847"]}],
                    "isDataGolden": true,
                    "samplesReadCounts": ["1000060"],
                    "samplingSpaceSizes": ["2065269"],
                    "totals": [{"values": ["15960"]}]
                },
                "columnHeader": {
                    "dimensions": ["ga:dimension12"],
                    "metricHeader": {
                        "metricHeaderEntries": [
                            {"type": "INTEGER", "name": "ga:users"}
                        ]
                    }
                }
            }
        ]}"""

        mock_creds = mock_credclass.from_json_keyfile_dict.return_value
        mock_creds.authorize.return_value = HttpMockSequence([
            ({'status': '200'}, self.valid_discovery),
            ({'status': '200'}, valid_response)
        ])

        results = analytics_user_counts(1074760, 1068728)

        self.assertEqual(results, {1074760: 847, 1068728: 15113})

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
            analytics_user_counts(1074760, 1068728)

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
            analytics_user_counts(1074760, 1068728)

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
            analytics_user_counts(1074760, 1068728)
