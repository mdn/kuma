from __future__ import unicode_literals

import mock
import pytest
import requests

from ..akismet import Akismet, AkismetError
from ..constants import CHECK_URL, HAM_URL, SPAM_URL, VERIFY_URL


def test_verify_empty_key(spam_check_everyone, constance_config):
    constance_config.AKISMET_KEY = ''
    client = Akismet()
    assert not client.ready
    assert client.key == ''


def test_verify_valid_key(spam_check_everyone, constance_config,
                          mock_requests):
    constance_config.AKISMET_KEY = 'api-key'
    mock_requests.post(VERIFY_URL, content=b'valid')
    client = Akismet()
    assert not mock_requests.called
    assert client.ready
    assert mock_requests.call_count == 1
    assert client.key == 'api-key'


def test_verify_invalid_key(spam_check_everyone, constance_config,
                            mock_requests):
    constance_config.AKISMET_KEY = 'api-key'
    mock_requests.post(VERIFY_URL, content=b'invalid')
    client = Akismet()
    assert not mock_requests.called
    assert not client.ready
    assert mock_requests.call_count == 1
    assert client.key == 'api-key'


def test_verify_invalid_key_wrong_response(spam_check_everyone,
                                           constance_config, mock_requests):
    constance_config.AKISMET_KEY = 'api-key'
    mock_requests.post(VERIFY_URL, content=b'fail')
    client = Akismet()
    assert not client.ready
    assert client.key == 'api-key'
    assert not client.verify_key()
    assert mock_requests.call_count == 2


@mock.patch('newrelic.agent.record_exception')
def test_exception_recording(mock_record_exception, spam_check_everyone,
                             constance_config, mock_requests):
    from requests.exceptions import HTTPError

    constance_config.AKISMET_KEY = 'api-key'
    exception = HTTPError('Nobody expects the Spanish inquisition')
    mock_requests.post(VERIFY_URL, exc=exception)
    client = Akismet()
    assert not client.ready
    assert mock_record_exception.called


def test_exception_attributes(spam_check_everyone, constance_config,
                              mock_requests):
    constance_config.AKISMET_KEY = 'comment'
    mock_requests.post(
        VERIFY_URL,
        content=b'uh uh',
        headers={'X-Akismet-Debug-Help': 'err0r!'},
    )

    client = Akismet()
    assert not client.verify_key()


def test_check_comment_ham(spam_check_everyone, constance_config,
                           mock_requests):
    constance_config.AKISMET_KEY = 'comment'
    mock_requests.post(VERIFY_URL, content=b'valid')
    client = Akismet()
    assert client.ready

    mock_requests.post(CHECK_URL, content=b'true')
    valid = client.check_comment('0.0.0.0', 'Mozilla',
                                 comment_content='yada yada')
    assert valid
    request_body = mock_requests.request_history[1].body
    assert 'user_ip=0.0.0.0' in request_body
    assert 'user_agent=Mozilla' in request_body
    assert 'comment_content=yada+yada' in request_body


def test_check_comment_spam(spam_check_everyone, constance_config,
                            mock_requests):
    constance_config.AKISMET_KEY = 'comment'
    mock_requests.post(VERIFY_URL, content=b'valid')
    mock_requests.post(CHECK_URL, content=b'false')
    client = Akismet()
    valid = client.check_comment('0.0.0.0', 'Mozilla',
                                 comment_content='yada yada')
    assert not valid


def test_check_comment_wrong_response(spam_check_everyone, constance_config,
                                      mock_requests):
    constance_config.AKISMET_KEY = 'comment'
    mock_requests.post(VERIFY_URL, content=b'valid')
    client = Akismet()
    mock_requests.post(CHECK_URL, content=b'wat', status_code=202)
    with pytest.raises(AkismetError) as excinfo:
        client.check_comment('0.0.0.0', 'Mozilla',
                             comment_content='yada yada')
    exc = excinfo.value
    assert exc.status_code == 202
    assert exc.debug_help == 'Not provided'
    assert isinstance(exc.response, requests.Response)


def test_submit_spam_success(spam_check_everyone, constance_config,
                             mock_requests):
    constance_config.AKISMET_KEY = 'spam'
    mock_requests.post(VERIFY_URL, content=b'valid')
    client = Akismet()
    mock_requests.post(
        SPAM_URL, content=client.submission_success.encode('utf-8'))
    result = client.submit_spam('0.0.0.0', 'Mozilla',
                                comment_content='spam. spam spam. spam.')
    assert result is None


def test_submit_spam_failure(spam_check_everyone, constance_config,
                             mock_requests):
    constance_config.AKISMET_KEY = 'spam'
    mock_requests.post(VERIFY_URL, content=b'valid')
    client = Akismet()
    mock_requests.post(SPAM_URL, content=b'something completely different')
    with pytest.raises(AkismetError) as excinfo:
        client.submit_spam('0.0.0.0', 'Mozilla',
                           comment_content='spam. eggs.')
    exc = excinfo.value
    assert exc.status_code == 200
    assert exc.debug_help == 'Not provided'
    assert isinstance(exc.response, requests.Response)


def test_submit_ham_success(spam_check_everyone, constance_config,
                            mock_requests):
    constance_config.AKISMET_KEY = 'spam'
    mock_requests.post(VERIFY_URL, content=b'valid')
    client = Akismet()
    mock_requests.post(
        HAM_URL, content=client.submission_success.encode('utf-8'))
    result = client.submit_ham('0.0.0.0', 'Mozilla',
                               comment_content='ham and bacon and pork.')
    assert result is None


def test_submit_ham_failure(spam_check_everyone, constance_config,
                            mock_requests):
    constance_config.AKISMET_KEY = 'spam'
    mock_requests.post(VERIFY_URL, content=b'valid')
    client = Akismet()
    mock_requests.post(HAM_URL, content=b'something completely different')
    with pytest.raises(AkismetError) as excinfo:
        client.submit_ham('0.0.0.0', 'Mozilla',
                          comment_content='eggs with ham. ham with eggs.')
    exc = excinfo.value
    assert exc.status_code == 200
    assert exc.debug_help == 'Not provided'
    assert isinstance(exc.response, requests.Response)
