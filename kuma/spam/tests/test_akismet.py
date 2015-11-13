import mock
import requests
import responses
from constance.test import override_config
from django.test import SimpleTestCase
from nose.plugins.attrib import attr
from waffle.models import Flag

from ..akismet import Akismet, AkismetError
from ..constants import (CHECK_URL_RE, HAM_URL_RE, SPAM_CHECKS_FLAG,
                         SPAM_URL_RE, VERIFY_URL_RE)


@attr('spam')
@override_config(AKISMET_KEY='api-key')
class AkismetClientTests(SimpleTestCase):

    def setUp(self):
        super(AkismetClientTests, self).setUp()
        responses.start()
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': True},
        )

    def tearDown(self):
        super(AkismetClientTests, self).tearDown()
        responses.stop()
        responses.reset()
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': None},
        )

    @override_config(AKISMET_KEY='')
    def test_verify_empty_key(self):
        client = Akismet()
        self.assertFalse(client.ready)
        self.assertEqual(client.key, '')

    def test_verify_valid_key(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')

        client = Akismet()
        self.assertEqual(len(responses.calls), 0)
        self.assertTrue(client.ready)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].response.text, 'valid')
        self.assertEqual(client.key, 'api-key')

    def test_verify_invalid_key(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='invalid')

        client = Akismet()
        self.assertEqual(len(responses.calls), 0)
        self.assertFalse(client.ready)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].response.text, 'invalid')
        self.assertEqual(client.key, 'api-key')

    def test_verify_invalid_key_wrong_response(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='fail')

        client = Akismet()
        self.assertFalse(client.ready)
        self.assertEqual(client.key, 'api-key')
        self.assertFalse(client.verify_key())
        self.assertEqual(len(responses.calls), 2)
        for call in responses.calls:
            self.assertEqual(call.response.text, 'fail')

    @mock.patch('newrelic.agent.record_exception')
    def test_exception_recording(self, record_exception_mock):
        from requests.exceptions import HTTPError

        exception = HTTPError('Nobody expects the Spanish inquisition')
        responses.add(responses.POST, VERIFY_URL_RE, body=exception)
        client = Akismet()
        self.assertFalse(client.ready)
        self.assertTrue(record_exception_mock.called)

    def test_exception_attributes(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='uh uh',
                      adding_headers={'X-Akismet-Debug-Help': 'err0r!'})

        client = Akismet()
        try:
            client.verify_key()
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 200)
            self.assertEqual(exc.debug_help, 'err0r!')
            self.assertIsInstance(exc.response, requests.Response)

    @override_config(AKISMET_KEY='comment')
    def test_check_comment_ham(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        client = Akismet()
        self.assertTrue(client.ready)

        responses.add(responses.POST, CHECK_URL_RE, body='true')
        valid = client.check_comment('0.0.0.0', 'Mozilla',
                                     comment_content='yada yada')
        self.assertTrue(valid)
        request_body = responses.calls[1].request.body
        self.assertIn('user_ip=0.0.0.0', request_body)
        self.assertIn('user_agent=Mozilla', request_body)
        self.assertIn('comment_content=yada+yada', request_body)

    @override_config(AKISMET_KEY='comment')
    def test_check_comment_spam(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        client = Akismet()
        responses.add(responses.POST, CHECK_URL_RE, body='false')
        valid = client.check_comment('0.0.0.0', 'Mozilla',
                                     comment_content='yada yada')
        self.assertFalse(valid)

    @override_config(AKISMET_KEY='comment')
    def test_check_comment_wrong_response(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        client = Akismet()
        responses.add(responses.POST, CHECK_URL_RE, body='wat', status=202)
        try:
            valid = client.check_comment('0.0.0.0', 'Mozilla',
                                         comment_content='yada yada')
            self.assertFalse(valid)
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 202)
            self.assertEqual(exc.debug_help, 'Not provided')
            self.assertIsInstance(exc.response, requests.Response)

    @override_config(AKISMET_KEY='spam')
    def test_submit_spam_success(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        client = Akismet()
        responses.add(responses.POST, SPAM_URL_RE,
                      body=client.submission_success)
        result = client.submit_spam('0.0.0.0', 'Mozilla',
                                    comment_content='spam. spam spam. spam.')
        self.assertIsNone(result)

    @override_config(AKISMET_KEY='spam')
    def test_submit_spam_failure(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        client = Akismet()
        responses.add(responses.POST, SPAM_URL_RE,
                      body='something completely different')
        try:
            client.submit_spam('0.0.0.0', 'Mozilla',
                               comment_content='spam. eggs.')
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 200)
            self.assertEqual(exc.debug_help, 'Not provided')
            self.assertIsInstance(exc.response, requests.Response)

    @override_config(AKISMET_KEY='spam')
    def test_submit_ham_success(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        client = Akismet()
        responses.add(responses.POST, HAM_URL_RE,
                      body=client.submission_success)
        result = client.submit_ham('0.0.0.0', 'Mozilla',
                                   comment_content='ham and bacon and pork.')
        self.assertIsNone(result)

    @override_config(AKISMET_KEY='spam')
    def test_submit_ham_failure(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        client = Akismet()
        responses.add(responses.POST, HAM_URL_RE,
                      body='something completely different')
        try:
            client.submit_ham('0.0.0.0', 'Mozilla',
                              comment_content='eggs with ham. ham with eggs.')
        except AkismetError as exc:
            self.assertEqual(exc.status_code, 200)
            self.assertEqual(exc.debug_help, 'Not provided')
            self.assertIsInstance(exc.response, requests.Response)
