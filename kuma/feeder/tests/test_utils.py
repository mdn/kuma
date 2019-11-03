

import socket
from datetime import datetime
from time import mktime, struct_time
from unittest import mock
from urllib.error import URLError

import jsonpickle
import pytest
from feedparser import FeedParserDict

from ..models import Entry, Feed
from ..utils import fetch_feed, save_entry, update_feed, update_feeds

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
        author='Jen Simmons',
        id='https://hacks.mozilla.org/?p=31957',
        link='https://hacks.mozilla.org/2018/02/its-resilient-css-week/',
        published='Mon, 26 Feb 2018 15:05:08 +0000',
        published_parsed=struct_time((2018, 2, 26, 15, 5, 8, 0, 57, 0)),
        summary='Jen Simmons celebrates resilient CSS',
        title='It\u2019s Resilient CSS Week',
    ), FeedParserDict(
        author='James Hobin',
        id='https://hacks.mozilla.org/?p=31946',
        link=('https://hacks.mozilla.org/2018/02/making-a-clap-sensing'
              '-web-thing/'),
        published='Thu, 22 Feb 2018 15:55:45 +0000',
        published_parsed=struct_time((2018, 2, 22, 15, 55, 45, 3, 53, 0)),
        summary=('The Project Things Gateway exists as a platform to bring'
                 ' all of your IoT devices together under a unified'
                 ' umbrella.'),
        title='Making a Clap-Sensing Web Thing',
    )],
    etag='W/"1da1fc6a456fd49c32a9291b38ec31ee-gzip"',
    feed=FeedParserDict(
        # Omited attributes: generator, generator_detail, language, links,
        # subtitle_detail, sy_updatefrequency, sy_updateperiod, title_detail,
        link='https://hacks.mozilla.org',
        subtitle='hacks.mozilla.org',
        title='Mozilla Hacks \u2013 the Web developer blog',
        updated='Mon, 26 Feb 2018 21:23:38 +0000',
        updated_parsed=struct_time((2018, 2, 26, 21, 23, 38, 0, 57, 0))),
    href='https://hacks.mozilla.org/feed/',
    status=200,
    updated='Mon, 26 Feb 2018 21:23:38 GMT',
    updated_parsed=struct_time((2018, 2, 26, 21, 23, 38, 0, 57, 0)),
    version='rss20')


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


def test_fetch_feed_sets_title(hacks_feed, mocked_parse):
    """A feed can update the title."""
    hacks_feed.title = 'Old Title'
    stream = fetch_feed(hacks_feed)
    assert stream
    feed = Feed.objects.get()
    assert feed.title == 'Mozilla Hacks \u2013 the Web developer blog'


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
    hacks_feed.title = 'Mozilla Hacks \u2013 the Web developer blog'
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


@pytest.mark.parametrize('entry_num', (0, 1))
def test_save_entry_new_items(hacks_feed, entry_num):
    """save_entry saves new entries to the database."""
    entry_raw = HACKS_PARSED.entries[entry_num]
    assert save_entry(hacks_feed, entry_raw)
    entry = Entry.objects.get()
    assert entry.guid == entry_raw.guid
    published = datetime.fromtimestamp(mktime(entry_raw.published_parsed))
    assert entry.last_published == published
    assert entry.raw


def test_save_entry_long_guid(hacks_feed):
    """A entry with a long GUID (usually an URL) is converted to a hash."""
    long_guid = 'https://example.com/a_%s_long_url' % '_'.join(['very'] * 100)
    entry_raw = modify_fpd(HACKS_PARSED.entries[0], guid=long_guid)
    assert save_entry(hacks_feed, entry_raw)
    entry = Entry.objects.get()
    assert entry.guid == '36d5f76416dcdf6beb8a01a937858d5a'


def test_save_entry_update_existing(hacks_feed):
    """save_entry updates an existing entry by GUID."""
    entry_raw = HACKS_PARSED.entries[0]
    Entry.objects.create(feed=hacks_feed, guid=entry_raw.guid, raw='old',
                         visible=False, last_published=datetime(2010, 1, 1))
    assert save_entry(hacks_feed, entry_raw)
    entry = Entry.objects.get()
    assert entry.raw != 'old'
    assert entry.visible
    assert entry.last_published == datetime(2018, 2, 26, 15, 5, 8)


def test_save_entry_no_change(hacks_feed):
    """save_entry returns False if no changes."""
    entry_raw = HACKS_PARSED.entries[0]
    Entry.objects.create(feed=hacks_feed, guid=entry_raw.guid,
                         raw=jsonpickle.encode(entry_raw),
                         visible=True,
                         last_published=datetime(2018, 2, 26, 15, 5, 8))
    assert not save_entry(hacks_feed, entry_raw)


def test_update_feed(hacks_feed, mocked_parse):
    """update_feed adds new entries."""
    count = update_feed(hacks_feed)
    assert count == 2
    assert Entry.objects.count() == 2


def test_update_feed_delete_old_entries(hacks_feed, mocked_parse):
    """update_feed deletes entries that exceed the maxiumum."""
    hacks_feed.keep = 1
    count = update_feed(hacks_feed)
    assert count == 2
    entry = Entry.objects.get()  # Just one entry
    assert entry.last_published == datetime(2018, 2, 26, 15, 5, 8)  # Is latest


@mock.patch('kuma.feeder.utils.fetch_feed')
def test_update_feed_no_feed_changes(mocked_fetch, hacks_feed):
    """if feed is stale, no entries are processed."""
    mocked_fetch.return_value = None
    count = update_feed(hacks_feed)
    assert count == 0


@mock.patch('kuma.feeder.utils.save_entry')
def test_update_feed_no_entry_changes(mocked_save, hacks_feed, mocked_parse):
    """if entries are stale, count is 0."""
    mocked_save.return_value = False
    count = update_feed(hacks_feed)
    assert count == 0


def test_update_feeds(hacks_feed, mocked_parse):
    """update_feeds adds new entries, resets timeout."""
    assert socket.getdefaulttimeout() is None
    count = update_feeds()
    assert count == 2
    assert Entry.objects.count() == 2
    assert socket.getdefaulttimeout() is None


def test_update_feeds_skip_disabled(hacks_feed):
    """update_feeds can skip updating disabled feeds."""
    hacks_feed.enabled = False
    hacks_feed.save()
    count = update_feeds(include_disabled=False)
    assert count == 0


@mock.patch('kuma.feeder.utils.update_feed')
def test_update_feeds_resets_timeout_on_exception(mock_update, hacks_feed):
    """update_feeds resets the socket timeout even on an exception."""
    assert socket.getdefaulttimeout() is None
    mock_update.side_effect = Exception('Failure')
    with pytest.raises(Exception):
        update_feeds()
    assert socket.getdefaulttimeout() is None
