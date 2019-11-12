

from datetime import datetime, timedelta
from uuid import uuid4

import jsonpickle
import pytest

from ..models import Bundle, Entry, Feed


@pytest.fixture
def bundle(db):
    """A test bundle."""
    return Bundle.objects.create(shortname='test-bundle')


@pytest.fixture
def feed(bundle):
    """A test feed."""
    feed = Feed.objects.create(
        shortname='test-feed',
        last_modified=datetime.now())
    bundle.feeds.add(feed)
    return feed


@pytest.fixture
def entries(feed):
    """A list of 10 test entries."""
    now = datetime.now()
    entries = []
    for day in range(10, 0, -1):
        entries.append(Entry.objects.create(
            feed=feed,
            guid=uuid4(),
            last_published=now - timedelta(days=day),
        ))
    return entries


def test_bundle_manager_recent_entries(entries):
    """Bundle.object.recent_entries returns recent entries."""
    recents = Bundle.objects.recent_entries('test-bundle')
    assert len(recents) == 10
    missing = Bundle.objects.recent_entries('tweets')
    assert not missing.exists()


def test_bundle_unicode(bundle):
    """str(Bundle) retuns the shortname."""
    assert str(bundle) == 'test-bundle'


def test_feed_unicode(feed):
    """str(Feed) retuns the shortname."""
    assert str(feed) == 'test-feed'


def test_feed_delete_old_entries(entries):
    """Feed.delete_old_entries removes old entries."""
    feed = entries[0].feed
    feed.keep = 5
    # Check that entries are ordered oldest first
    assert entries[0].last_published < entries[-1].last_published
    assert 0 < feed.keep < len(entries)
    feed.delete_old_entries()

    remaining = list(Entry.objects.all())
    assert len(remaining) == feed.keep
    expected = list(reversed(entries[-feed.keep:]))
    assert remaining == expected


def test_feed_delete_old_entries_keep_is_0(entries):
    """Feed.delete_old_entries does nothing if .keep is not positive."""
    feed = entries[0].feed
    assert feed.keep == 0
    feed.delete_old_entries()
    assert Entry.objects.count() == len(entries)  # None deleted


def test_entry_unicode(feed):
    """str(Entry) returns feed and GUID."""
    entry = Entry(
        feed=feed,
        guid='374f4947-e6be-4fdd-9a66-6535dc79a722',
        last_published=datetime(2018, 2, 27, 16, 3))

    assert str(entry) == 'test-feed: 374f4947-e6be-4fdd-9a66-6535dc79a722'


def test_entry_parsed(feed):
    """Entry.parsed returns the unpickled raw content."""
    data = {
        "title": "Episode #1",
        "content": "<p>Here's the first entry of my monthly series.</p>",
        "published": datetime(2014, 2, 7)
    }
    entry = Entry(
        feed=feed,
        guid='4a2f0033-f987-4c07-a9bf-d2fc960c3c56',
        last_published=datetime(2014, 2, 7),
        raw=jsonpickle.encode(data))
    assert entry.parsed == data
