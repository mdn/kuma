from __future__ import unicode_literals

import mock
import pytest
import requests

from kuma.scrape.scraper import Requester, Scraper
from kuma.scrape.sources import Source

#
# Requester tests (mostly for coverage)
#


def test_session():
    """A session is created once on request."""
    requester = Requester('example.com', True)
    session = requester.session
    assert isinstance(session, requests.Session)
    session2 = requester.session
    assert session is session2


def test_request():
    """A successful request calls raise_for_status by default."""
    requester = Requester('example.com', True)
    mock_session = mock.Mock(spec_set=['get'])
    mock_response = mock.Mock(spec_set=['raise_for_status', 'status_code'])
    mock_response.status_code = 400
    mock_session.get.return_value = mock_response
    requester._session = mock_session

    response = requester.request('/path')
    assert response is mock_response
    mock_session.get.assert_called_once_with(
        'https://example.com/path', timeout=1.0)
    mock_response.raise_for_status.assert_called_once_with()


def test_request_no_raise():
    """The call to raise_for_status can be omitted."""
    requester = Requester('example.net', False)
    mock_session = mock.Mock(spec_set=['get'])
    mock_response = mock.Mock(spec_set=['raise_for_status', 'status_code'])
    mock_response.status_code = 400
    mock_session.get.return_value = mock_response
    requester._session = mock_session

    response = requester.request('/path', raise_for_status=False)
    assert response is mock_response
    mock_session.get.assert_called_once_with(
        'http://example.net/path', timeout=1.0)
    assert not mock_response.raise_for_status.called


@mock.patch('kuma.scrape.scraper.time.sleep')
def test_timeout_success(mock_sleep):
    """Requests are retried with back off after a Timeout."""
    requester = Requester('example.com', True)
    mock_session = mock.Mock(spec_set=['get'])
    mock_response = mock.Mock(spec_set=['status_code'])
    mock_response.status_code = 200
    mock_session.get.side_effect = [
        requests.exceptions.Timeout(),
        requests.exceptions.Timeout(),
        mock_response]
    requester._session = mock_session

    response = requester.request('/path', raise_for_status=False)
    assert response is mock_response
    full_path = 'https://example.com/path'
    expected_calls = [
        mock.call(full_path, timeout=1.0),
        mock.call(full_path, timeout=2.0),  # Timeout doubles
        mock.call(full_path, timeout=4.0),  # Timeout doubles again
    ]
    assert mock_session.get.call_args_list == expected_calls
    expected_sleep_calls = [mock.call(1.0), mock.call(2.0)]
    assert mock_sleep.call_args_list == expected_sleep_calls


def test_connectionerror_success():
    """Requests are retried after expected exceptions."""
    requester = Requester('example.com', True)
    mock_session = mock.Mock(spec_set=['get'])
    mock_response = mock.Mock(spec_set=['status_code'])
    mock_response.status_code = 200
    mock_session.get.side_effect = [
        requests.exceptions.ConnectionError(),
        requests.exceptions.ConnectionError(),
        mock_response]
    requester._session = mock_session

    response = requester.request('/path', raise_for_status=False)
    assert response is mock_response
    full_path = 'https://example.com/path'
    expected_calls = [mock.call(full_path, timeout=1.0)] * 3
    assert mock_session.get.call_args_list == expected_calls


@mock.patch('kuma.scrape.scraper.time.sleep')
def test_timeout_failure(mock_sleep):
    """Request fail after too many Timeouts."""
    attempts = 7
    assert Requester.MAX_ATTEMPTS == attempts
    requester = Requester('example.com', True)
    mock_session = mock.Mock(spec_set=['get'])
    mock_session.get.side_effect = [requests.exceptions.Timeout] * attempts
    requester._session = mock_session

    with pytest.raises(requests.exceptions.Timeout):
        requester.request('/path', raise_for_status=False)
    full_path = 'https://example.com/path'
    times = [2.0 ** attempt for attempt in range(attempts)]  # 1, 2, 4, 8...
    expected_calls = [mock.call(full_path, timeout=time) for time in times]
    assert mock_session.get.call_args_list == expected_calls
    expected_sleep_calls = [mock.call(time) for time in times]
    assert mock_sleep.call_args_list == expected_sleep_calls


rate_limit_tests = {
    'Retry-After as seconds': ('65', 65),
    'Retry-After as date': ('Wed, 21 Oct 2015 07:28:00 GMT', 30),
    'Retry-After as 0 seconds': ('0', 1),
}


@mock.patch('kuma.scrape.scraper.time.sleep')
@pytest.mark.parametrize('retry_after,sleep_time',
                         rate_limit_tests.values(),
                         ids=list(rate_limit_tests))
def test_request_429_is_retried(mock_sleep, retry_after, sleep_time):
    """Requests are retried after a 429 Too Many Requests status."""
    requester = Requester('example.com', True)
    mock_session = mock.Mock(spec_set=['get'])
    mock_response1 = mock.Mock(spec_set=['status_code', 'headers'])
    mock_response1.status_code = 429
    mock_response1.headers.get.return_value = retry_after
    mock_response2 = mock.Mock(spec_set=['status_code'])
    mock_response2.status_code = 200
    mock_session.get.side_effect = [mock_response1, mock_response2]
    requester._session = mock_session

    response = requester.request('/path', raise_for_status=False)
    assert response is mock_response2
    full_path = 'https://example.com/path'
    expected_calls = [mock.call(full_path, timeout=1.0)] * 2
    assert mock_session.get.call_args_list == expected_calls
    mock_response1.headers.get.assert_called_once_with('retry-after', 30)
    mock_sleep.assert_called_once_with(sleep_time)


@mock.patch('kuma.scrape.scraper.time.sleep')
def test_request_504_is_retried(mock_sleep):
    """Requests are retried after a 504 Gateway Timeout status."""
    requester = Requester('example.com', True)
    mock_session = mock.Mock(spec_set=['get'])
    mock_response1 = mock.Mock(spec_set=['status_code'])
    mock_response1.status_code = 504
    mock_response2 = mock.Mock(spec_set=['status_code'])
    mock_response2.status_code = 200
    mock_session.get.side_effect = [mock_response1, mock_response2]
    requester._session = mock_session

    response = requester.request('/path', raise_for_status=False)
    assert response is mock_response2
    full_path = 'https://example.com/path'
    expected_calls = [
        mock.call(full_path, timeout=1.0),
        mock.call(full_path, timeout=2.0),
    ]
    assert mock_session.get.call_args_list == expected_calls
    mock_sleep.assert_called_once_with(1)


#
# Tests for Scraper
#

class FakeSource(Source):
    """A Fake source for testing scraping."""

    PARAM_NAME = 'name'
    OPTIONS = {
        'length': ('int', 0),         # Number of gather rounds until done
        'depth': ('int', 0),          # Generations of sources emitted
        'error': ('bool', False),     # Set state to STATE_ERROR
    }

    def gather(self, requester, storage):
        """
        Run for [length] rounds and emit [depth] generations of sources.

        This does nothing except exercise all the branches of Scraper.scrape.
        """
        sources = []
        if self.state == self.STATE_INIT:
            self.remaining_length = self.length
            self.state = self.STATE_PREREQ

        assert self.state == self.STATE_PREREQ
        if self.depth:
            sources.append(('fake', "%s%d" % (self.name, self.depth),
                            {'length': self.length,
                            'depth': self.depth - 1}))

        if self.remaining_length == 0:
            if self.error:
                self.state = self.STATE_ERROR
            else:
                self.state = self.STATE_DONE
        else:
            self.remaining_length -= 1

        return sources


@pytest.fixture()
def scraper():
    """Setup a test Scraper that handles FakeSource sources."""
    scraper = Scraper()
    scraper.source_types['fake'] = FakeSource
    return scraper


@pytest.yield_fixture()
def mock_logger():
    with mock.patch('kuma.scrape.scraper.logger') as mock_logger:
        yield mock_logger


def test_add_new_source(scraper):
    """The add_source method initializes a source."""
    assert scraper.add_source('fake', 'bob')
    source = scraper.sources['fake:bob']
    assert isinstance(source, FakeSource)
    assert source.name == 'bob'


def test_add_existing_source(scraper):
    """Adding a existing source returns True if options were updated."""
    assert scraper.add_source('fake', 'jane')
    assert not scraper.add_source('fake', 'jane')
    assert scraper.add_source('fake', 'jane', length=1)
    assert not scraper.add_source('fake', 'jane', length=1)


def test_scrape(scraper):
    """The scraper will loop through sources until complete."""
    scraper.add_source('fake', 'loop', length=2, depth=2)
    sources = scraper.scrape()
    assert set(sources.keys()) == {'fake:loop', 'fake:loop2', 'fake:loop21'}


def test_scrape_error(scraper):
    """The scraper will complete if a source is errored."""
    scraper.add_source('fake', 'will_error', error=True)
    sources = scraper.scrape()
    source = sources['fake:will_error']
    assert source.state == source.STATE_ERROR


def test_scrape_none(scraper):
    """A scraper with no sources returns early."""
    sources = scraper.scrape()
    assert not sources


def test_warn_percent_in_param(scraper, mock_logger):
    """
    The scraper will warn if there is a percent in a source.

    This indicates a JSON-encoded URL was not decoded.
    """
    scraper.add_source('fake', 'loop%0d', depth=1)
    scraper.scrape()
    expected_fmt = 'Source "%s" has a percent in deps'
    mock_logger.warn.assert_called_once_with(expected_fmt, 'fake:loop%0d')


def test_warn_dependency_block(scraper, mock_logger):
    """
    The scraper will warn if a dependency block is detected.

    If no progress is made in a loop, it implies that a dependency is in
    error, and further loops will not make any further progress.
    """
    scraper.add_source('fake', 'bad_document', length=2, error=True)
    scraper.scrape()
    expected_msg = 'Dependency block detected. Aborting after %d second%s.'
    mock_logger.warn.assert_called_once_with(expected_msg, 1, '')
