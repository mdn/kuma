# -*- coding: utf-8 -*-
import socket
from datetime import datetime
from time import struct_time
from urllib2 import URLError

import mock
import pytest
from feedparser import FeedParserDict

from ..models import Feed
from ..utils import fetch_feed

# URL of the Hacks blog RSS 2.0 feed
HACKS_URL = 'https://hacks.mozilla.org/feed/'

# A truncated result from parsing the Hacks blogs with feedparser
HACKS_PARSED = FeedParserDict(
    # Omited attributes: encoding, headers, namespaces
    bozo=0,
    entries=[FeedParserDict(
        # Omited attributes: author_detail, authors, content, guidislink,
        # links, summary_detail, tags, title_detail, comments, slash_comments,
        # wfw_commentrss
        author=u'Jen Simmons',
        id=u'https://hacks.mozilla.org/?p=31957',
        link=u'https://hacks.mozilla.org/2018/02/its-resilient-css-week/',
        published=u'Mon, 26 Feb 2018 15:05:08 +0000',
        published_parsed=struct_time((2018, 2, 26, 15, 5, 8, 0, 57, 0)),
        summary=u'Jen Simmons celebrates resilient CSS',
        title=u'It\u2019s Resilient CSS Week',
    ), FeedParserDict(
        author=u'James Hobin',
        id=u'https://hacks.mozilla.org/?p=31946',
        link=(u'https://hacks.mozilla.org/2018/02/making-a-clap-sensing'
              u'-web-thing/'),
        published=u'Thu, 22 Feb 2018 15:55:45 +0000',
        published_parsed=struct_time((2018, 2, 22, 15, 55, 45, 3, 53, 0)),
        summary=(u'The Project Things Gateway exists as a platform to bring'
                 u' all of your IoT devices together under a unified'
                 u' umbrella.'),
        title=u'Making a Clap-Sensing Web Thing',
    )],
    etag=u'W/"1da1fc6a456fd49c32a9291b38ec31ee-gzip"',
    feed=FeedParserDict(
        # Omited attributes: generator, generator_detail, language, links,
        # subtitle_detail, sy_updatefrequency, sy_updateperiod, title_detail,
        link=u'https://hacks.mozilla.org',
        subtitle=u'hacks.mozilla.org',
        title=u'Mozilla Hacks \u2013 the Web developer blog',
        updated=u'Mon, 26 Feb 2018 21:23:38 +0000',
        updated_parsed=struct_time((2018, 2, 26, 21, 23, 38, 0, 57, 0))),
    href=u'https://hacks.mozilla.org/feed/',
    status=200,
    updated='Mon, 26 Feb 2018 21:23:38 GMT',
    updated_parsed=struct_time((2018, 2, 26, 21, 23, 38, 0, 57, 0)),
    version=u'rss20')


def modify_fpd(parsed, **kwargs):
    """Create a new FeedParserDict, overriding some values."""
    response = FeedParserDict(**parsed.copy())
    for key, value in kwargs.items():
        response[key] = value
    return response


@pytest.fixture
def hacks_feed(db):
    """A Feed for the Hacks Blog."""
    return Feed.objects.create(
        shortname='moz-hacks',
        url=HACKS_URL,
        last_modified=datetime(2018, 2, 25)
    )


@pytest.fixture
def mocked_parse():
    """Return test feedparser data instead of making an HTTP GET."""
    with mock.patch('kuma.feeder.utils.feedparser.parse') as mock_parse:
        mock_parse.return_value = HACKS_PARSED
        yield mock_parse


def test_fetch_feed(hacks_feed, mocked_parse):
    """A regular fetch succeeds."""
    stream = fetch_feed(hacks_feed)
    assert stream
    feed = Feed.objects.get()
    assert feed.url == HACKS_URL
    assert feed.etag == 'W/"1da1fc6a456fd49c32a9291b38ec31ee-gzip"'
    assert feed.last_modified == datetime(2018, 2, 26, 21, 23, 38)
    assert feed.enabled
    assert feed.disabled_reason == ''


@pytest.mark.parametrize('orig_modified', (None, datetime(2018, 2, 1)))
def test_fetch_feed_sets_modified(hacks_feed, mocked_parse, orig_modified):
    """A feed's last_modified date is updated."""
    hacks_feed.last_modified = orig_modified
    stream = fetch_feed(hacks_feed)
    assert stream
    feed = Feed.objects.get()
    assert feed.last_modified == datetime(2018, 2, 26, 21, 23, 38)


def test_fetch_feed_sets_enabled(hacks_feed, mocked_parse):
    """A disabled feed is enabled."""
    hacks_feed.enabled = False
    stream = fetch_feed(hacks_feed)
    assert stream
    feed = Feed.objects.get()
    assert feed.enabled


def test_fetch_feed_redirect(hacks_feed, mocked_parse):
    """If redirected, the URL is updated but the feed is not processed."""
    new_url = 'https://hacks.example.com/feed'
    response = modify_fpd(HACKS_PARSED, status=301, url=new_url)
    mocked_parse.return_value = response
    stream = fetch_feed(hacks_feed)
    assert not stream
    feed = Feed.objects.get()
    assert feed.enabled
    assert feed.url == new_url


@pytest.mark.parametrize('enabled', ('enabled', 'disabled'))
def test_fetch_feed_unchanged(hacks_feed, mocked_parse, enabled):
    """If the ETag matches, the feed is enabled but not processed."""
    hacks_feed.last_modified = datetime(2018, 2, 26, 21, 23, 38)
    hacks_feed.etag = 'W/"1da1fc6a456fd49c32a9291b38ec31ee-gzip"'
    hacks_feed.enabled = (enabled == 'enabled')
    hacks_feed.save()  # Won't be saved in enabled case
    mocked_parse.return_value = modify_fpd(HACKS_PARSED, status=304)
    stream = fetch_feed(hacks_feed)
    assert not stream
    feed = Feed.objects.get()
    assert feed.enabled


@pytest.mark.parametrize('status', (404, 410))
def test_fetch_feed_missing(hacks_feed, mocked_parse, status):
    """If the feed is gone, it is disabled."""
    mocked_parse.return_value = modify_fpd(HACKS_PARSED, status=status)
    stream = fetch_feed(hacks_feed)
    assert not stream
    feed = Feed.objects.get()
    assert not feed.enabled
    expected = {
        404: 'This is not a feed or it has been removed!',
        410: 'This feed has been removed!',
    }[status]
    assert feed.disabled_reason == expected


def test_fetch_feed_timeout(mocked_parse, hacks_feed, settings):
    """If a feed times out, it is disabled."""
    settings.FEEDER_TIMEOUT = 10
    mocked_parse.return_value = FeedParserDict(
        bozo=1,
        bozo_exception=URLError(reason=socket.timeout('timed out')))
    stream = fetch_feed(hacks_feed)
    assert stream is None
    feed = Feed.objects.get()
    assert feed.etag == ''
    assert not feed.enabled
    expected_reason = "This feed didn't respond after 10 seconds"
    assert feed.disabled_reason == expected_reason


def test_fetch_feed_exception(mocked_parse, hacks_feed):
    """If a feed encounters an exception, it is disabled."""
    mocked_parse.return_value = FeedParserDict(
        bozo=1,
        bozo_exception=Exception('I am grumpy today.'))
    stream = fetch_feed(hacks_feed)
    assert stream is None
    feed = Feed.objects.get()
    assert not feed.enabled
    expected_reason = "Error while reading the feed: 500 __ I am grumpy today."
    assert feed.disabled_reason == expected_reason


def test_fetch_feed_unknown_issue(mocked_parse, hacks_feed):
    """If a feed encounters an unknown issue, it is disabled."""
    mocked_parse.return_value = FeedParserDict(bozo=1)
    stream = fetch_feed(hacks_feed)
    assert stream is None
    feed = Feed.objects.get()
    assert not feed.enabled
    expected_reason = "Error while reading the feed: 500 __ "
    assert feed.disabled_reason == expected_reason
