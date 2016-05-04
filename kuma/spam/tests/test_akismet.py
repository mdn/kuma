from constance.test import override_config
from waffle.models import Flag
import mock
import pytest
import requests
import requests_mock

from django.test import SimpleTestCase

from ..akismet import Akismet, AkismetError
from ..constants import (CHECK_URL, HAM_URL, SPAM_CHECKS_FLAG,
                         SPAM_URL, VERIFY_URL)


@pytest.mark.spam
@override_config(AKISMET_KEY='api-key')
class AkismetClientTests(SimpleTestCase):

    def setUp(self):
        super(AkismetClientTests, self).setUp()
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': True},
        )

    def tearDown(self):
        super(AkismetClientTests, self).tearDown()
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': None},
        )

    @override_config(AKISMET_KEY='')
    def test_verify_empty_key(self):
        client = Akismet()
        self.assertFalse(client.ready)
        self.assertEqual(client.key, '')

    @requests_mock.mock()
    def test_verify_valid_key(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        client = Akismet()
        self.assertFalse(mock_requests.called)
        self.assertTrue(client.ready)
        self.assertEqual(mock_requests.call_count, 1)
        self.assertEqual(client.key, 'api-key')

    @requests_mock.mock()
    def test_verify_invalid_key(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='invalid')
        client = Akismet()
        self.assertFalse(mock_requests.called)
        self.assertFalse(client.ready)
        self.assertEqual(mock_requests.call_count, 1)
        self.assertEqual(client.key, 'api-key')

    @requests_mock.mock()
    def test_verify_invalid_key_wrong_response(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='fail')
        client = Akismet()
        self.assertFalse(client.ready)
        self.assertEqual(client.key, 'api-key')
        self.assertFalse(client.verify_key())
        self.assertEqual(mock_requests.call_count, 2)

    @requests_mock.mock()
    @mock.patch('newrelic.agent.record_exception')
    def test_exception_recording(self, mock_requests, mock_record_exception):
        from requests.exceptions import HTTPError

        exception = HTTPError('Nobody expects the Spanish inquisition')
        mock_requests.post(VERIFY_URL, exc=exception)
        client = Akismet()
        self.assertFalse(client.ready)
        self.assertTrue(mock_record_exception.called)

    @requests_mock.mock()
    def test_exception_attributes(self, mock_requests):
        mock_requests.post(
            VERIFY_URL,
            content='uh uh',
            headers={'X-Akismet-Debug-Help': 'err0r!'},
        )

        client = Akismet()
        try:
            client.verify_key()
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 200)
            self.assertEqual(exc.debug_help, 'err0r!')
            self.assertIsInstance(exc.response, requests.Response)

    @override_config(AKISMET_KEY='comment')
    @requests_mock.mock()
    def test_check_comment_ham(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        client = Akismet()
        self.assertTrue(client.ready)

        mock_requests.post(CHECK_URL, content='true')
        valid = client.check_comment('0.0.0.0', 'Mozilla',
                                     comment_content='yada yada')
        self.assertTrue(valid)
        request_body = mock_requests.request_history[1].body
        self.assertIn('user_ip=0.0.0.0', request_body)
        self.assertIn('user_agent=Mozilla', request_body)
        self.assertIn('comment_content=yada+yada', request_body)

    @override_config(AKISMET_KEY='comment')
    @requests_mock.mock()
    def test_check_comment_spam(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content='false')
        client = Akismet()
        valid = client.check_comment('0.0.0.0', 'Mozilla',
                                     comment_content='yada yada')
        self.assertFalse(valid)

    @override_config(AKISMET_KEY='comment')
    @requests_mock.mock()
    def test_check_comment_wrong_response(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        client = Akismet()
        mock_requests.post(CHECK_URL, content='wat', status_code=202)
        try:
            valid = client.check_comment('0.0.0.0', 'Mozilla',
                                         comment_content='yada yada')
            self.assertFalse(valid)
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 202)
            self.assertEqual(exc.debug_help, 'Not provided')
            self.assertIsInstance(exc.response, requests.Response)

    @override_config(AKISMET_KEY='spam')
    @requests_mock.mock()
    def test_submit_spam_success(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        client = Akismet()
        mock_requests.post(SPAM_URL, content=client.submission_success)
        result = client.submit_spam('0.0.0.0', 'Mozilla',
                                    comment_content='spam. spam spam. spam.')
        self.assertIsNone(result)

    @override_config(AKISMET_KEY='spam')
    @requests_mock.mock()
    def test_submit_spam_failure(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        client = Akismet()
        mock_requests.post(SPAM_URL, content='something completely different')
        try:
            client.submit_spam('0.0.0.0', 'Mozilla',
                               comment_content='spam. eggs.')
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 200)
            self.assertEqual(exc.debug_help, 'Not provided')
            self.assertIsInstance(exc.response, requests.Response)

    @override_config(AKISMET_KEY='spam')
    @requests_mock.mock()
    def test_submit_ham_success(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        client = Akismet()
        mock_requests.post(HAM_URL, content=client.submission_success)
        result = client.submit_ham('0.0.0.0', 'Mozilla',
                                   comment_content='ham and bacon and pork.')
        self.assertIsNone(result)

    @override_config(AKISMET_KEY='spam')
    @requests_mock.mock()
    def test_submit_ham_failure(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        client = Akismet()
        mock_requests.post(HAM_URL, content='something completely different')
        try:
            client.submit_ham('0.0.0.0', 'Mozilla',
                              comment_content='eggs with ham. ham with eggs.')
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 200)
            self.assertEqual(exc.debug_help, 'Not provided')
            self.assertIsInstance(exc.response, requests.Response)
