

import logging
import socket
from datetime import datetime
from hashlib import md5
from time import mktime

import feedparser
import jsonpickle
from django.conf import settings
from django.utils.encoding import smart_bytes
from django.utils.six.moves.urllib.error import URLError

from .models import Entry, Feed

log = logging.getLogger('kuma.feeder')


def update_feeds(include_disabled=True):
    """
    Update all feeds, returning the number of new entries.

    Keyword arguments:
    include_disabled - Include feeds with enabled=False
    """
    feeds = Feed.objects.all()
    if not include_disabled:
        feeds = feeds.filter(enabled=True)

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(settings.FEEDER_TIMEOUT)

    new_entry_count = 0
    try:
        for feed in feeds:
            new_entry_count += update_feed(feed)
    finally:
        socket.setdefaulttimeout(old_timeout)

    return new_entry_count


def update_feed(feed):
    """
    Update a single feed.

    Returns number of newly fetched entries.
    """
    new_entry_count = 0

    stream = fetch_feed(feed)

    if stream:
        log.debug('Processing %s (%s): %s' % (feed.title, feed.shortname,
                                              feed.url))
        for entry in stream.entries:
            if save_entry(feed, entry):
                new_entry_count += 1

        # Remove old entries if applicable.
        feed.delete_old_entries()

    return new_entry_count


def fetch_feed(feed):
    """
    Fetch a feed from its URL and update its metadata if necessary.

    Returns stream if feed had updates, None otherwise.

    A long, long time ago, this code was borrowed from
    "planet/planet/.__init__.py channel update", which may not be
    https://github.com/mozilla/planet-source/blob/master/trunk/planet/spider.py
    """
    dirty_feed = False
    has_updates = False

    if feed.last_modified is None:
        feed.last_modified = datetime(1975, 1, 10)
    log.debug("feed id=%s feed url=%s etag=%s last_modified=%s" % (
        feed.shortname, feed.url, feed.etag, str(feed.last_modified)))
    stream = feedparser.parse(feed.url, etag=feed.etag or '',
                              modified=feed.last_modified.timetuple())

    url_status = 500
    if 'status' in stream:
        url_status = stream.status

    elif (stream.bozo and
          'bozo_exception' in stream and
          isinstance(stream.bozo_exception, URLError) and
          isinstance(stream.bozo_exception.reason, socket.timeout)):
        url_status = 408

    if url_status == 301 and ('entries' in stream and
                              len(stream.entries) > 0):
        # TODO: Should the feed be processed this round as well?
        log.info("Feed has moved from <%s> to <%s>", feed.url, stream.url)
        feed.url = stream.url
        dirty_feed = True

    elif url_status == 304:
        log.debug("Feed unchanged")
        if not feed.enabled:
            feed.enabled = True
            dirty_feed = True

    elif url_status == 404:
        log.info("Not a Feed or Feed %s is gone", feed.url)
        feed.enabled = False
        feed.disabled_reason = "This is not a feed or it has been removed!"
        dirty_feed = True

    elif url_status == 410:
        log.info("Feed %s gone", feed.url)
        feed.enabled = False
        feed.disabled_reason = "This feed has been removed!"
        dirty_feed = True

    elif url_status == 408:
        feed.enabled = False
        feed.disabled_reason = ("This feed didn't respond after %d seconds" %
                                settings.FEEDER_TIMEOUT)
        dirty_feed = True

    elif url_status >= 400:
        feed.enabled = False
        bozo_msg = ""
        if 1 == stream.bozo and 'bozo_exception' in stream.keys():
            log.error('Unable to fetch %s Exception: %s',
                      feed.url, stream.bozo_exception)
            bozo_msg = stream.bozo_exception
        feed.disabled_reason = ("Error while reading the feed: %s __ %s" %
                                (url_status, bozo_msg))
        dirty_feed = True
    else:
        # We've got a live one...
        if not feed.enabled or feed.disabled_reason:
            # Reset disabled status.
            feed.enabled = True
            feed.disabled_reason = ''
            dirty_feed = True
        has_updates = True

    if ('etag' in stream and stream.etag != feed.etag and
            stream.etag is not None):
        log.info("New etag %s" % stream.etag)
        feed.etag = stream.etag
        dirty_feed = True

    if 'modified_parsed' in stream:
        stream_mod = datetime.fromtimestamp(mktime(stream.modified_parsed))
        if stream_mod != feed.last_modified:
            log.info("New last_modified %s" % stream_mod)
            feed.last_modified = stream_mod
            dirty_feed = True

    if 'feed' in stream and 'title' in stream.feed:
        if feed.title != stream.feed.title:
            feed.title = stream.feed.title
            dirty_feed = True

    if dirty_feed:
        dirty_feed = False
        log.debug("Feed %s changed, updating db" % feed)
        feed.save()

    return has_updates and stream or None


def save_entry(feed, entry):
    """Save a new entry or update an existing one."""
    json_entry = jsonpickle.encode(entry)

    max_guid_length = Entry._meta.get_field('guid').max_length
    if len(entry.guid) <= max_guid_length:
        entry_guid = entry.guid
    else:
        entry_guid = md5(smart_bytes(entry.guid)).hexdigest()

    last_published = datetime.fromtimestamp(mktime(entry.published_parsed))

    entry, created = Entry.objects.get_or_create(
        feed=feed, guid=entry_guid,
        defaults={'raw': json_entry, 'visible': True,
                  'last_published': last_published})
    if not created:
        # Did the entry change?
        changed = (entry.raw != json_entry or
                   not entry.visible or
                   entry.last_published != last_published)
        if changed:
            entry.raw = json_entry
            entry.visible = True
            entry.last_published = last_published
            entry.save()
            return True
    return created
