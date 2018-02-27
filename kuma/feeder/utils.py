import logging
import socket
from datetime import datetime
from hashlib import md5
from time import strftime

import feedparser
import jsonpickle
from django.conf import settings
from django.db import IntegrityError
from django.utils.encoding import smart_str

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

    try:
        stream = fetch_feed(feed)

        if stream:
            log.debug('Processing %s: %s' % (feed.shortname, feed.url))

            if 'feed' in stream and 'title' in stream.feed:
                log.debug('Processing title: %s', stream.feed.title)

            dirty_feed = False
            if ('feed' in stream and 'title' in stream.feed and
                    feed.title != stream.feed.title):
                feed.title = stream.feed.title
                dirty_feed = True
            else:
                if ('feed' not in stream) or ('title' not in stream.feed):
                    log.warn("Feed doesn't have a title property")
                    log.info(stream)

            if dirty_feed:
                try:
                    feed.save()
                except KeyboardInterrupt:
                    raise
                except Exception, x:
                    log.error("Unable to update feed")
                    log.exception(x)

            for entry in stream.entries:
                if save_entry(feed, entry):
                    new_entry_count += 1

            # Remove old entries if applicable.
            feed.delete_old_entries()

    except KeyboardInterrupt:
        raise
    except Exception as e:
        log.error("General Error starting loop: %s", e)
        log.exception(e)

    return new_entry_count


def fetch_feed(feed):
    """
    Fetch a feed from its URL and update its metadata if necessary.

    Returns stream if feed had updates, None otherwise.
    """
    dirty_feed = False
    has_updates = False

    if feed.etag is None:
        feed.etag = ''
    if feed.last_modified is None:
        feed.last_modified = datetime(1975, 1, 10)
    log.debug("feed id=%s feed url=%s etag=%s last_modified=%s" % (
        feed.shortname, feed.url, feed.etag, str(feed.last_modified)))
    try:
        stream = feedparser.parse(feed.url, etag=feed.etag,
                                  modified=feed.last_modified.timetuple())
    except UnicodeDecodeError:
        print(feed.url)

    # Next 70 lines of code from planet/planet/.__init__.py channel update
    url_status = '500'

    if 'status' in stream:
        url_status = str(stream.status)

    elif 'entries' in stream and len(stream.entries) > 0:
        url_status = '200'

    elif (stream.bozo and
            stream.bozo_exception.__class__.__name__ == 'Timeout'):
        url_status = '408'

    if url_status == '301' and ('entries' in stream and
                                len(stream.entries) > 0):
        log.info("Feed has moved from <%s> to <%s>", feed.url, stream.url)
        feed.url = stream.url
        dirty_feed = True

    elif url_status == '304':
        log.debug("Feed unchanged")
        if not feed.enabled:
            feed.enabled = True
            dirty_feed = True

    elif url_status == '404':
        log.info("Not a Feed or Feed %s is gone", feed.url)
        feed.enabled = False
        feed.disabled_reason = ("This is not a feed or it's "
                                "been removed removed!")
        dirty_feed = True

    elif url_status == '410':
        log.info("Feed %s gone", feed.url)
        feed.enabled = False
        feed.disabled_reason = "This feed has been removed!"
        dirty_feed = True

    elif url_status == '408':
        feed.enabled = False
        feed.disabled_reason = ("This feed didn't respond "
                                "after %d seconds" %
                                settings.FEEDER_TIMEOUT)
        dirty_feed = True

    elif int(url_status) >= 400:
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

    if ('modified' in stream and
            stream.modified_parsed != feed.last_modified):
        feed.last_modified = strftime("%Y-%m-%d %H:%M:%S",
                                      stream.modified_parsed)
        log.info("New last_modified %s" % feed.last_modified)
        dirty_feed = True

    if dirty_feed:
        try:
            dirty_feed = False
            log.debug("Feed %s changed, updating db" % feed)
            feed.save()
        except KeyboardInterrupt:
            raise
        except Exception, x:
            log.error("Unable to update feed")
            log.exception(x)

    return has_updates and stream or None


def save_entry(feed, entry):
    """Save a new entry to the database."""
    try:
        json_entry = jsonpickle.encode(entry)
        entry_guid = ''

        if ('guid' in entry and
            (len(entry.guid) <=
                Entry._meta.get_field_by_name('guid')[0].max_length)):
            entry_guid = entry.guid
        else:
            entry_guid = md5(smart_str(json_entry)).hexdigest()

        if 'updated_parsed' in entry:
            yr, mon, d, hr, min, sec = entry.updated_parsed[:-3]
            last_publication = datetime.datetime(yr, mon, d, hr, min, sec)
        else:
            log.warn("Entry has no updated field, faking it")
            last_publication = datetime.now()

        new_entry = Entry(feed=feed, guid=entry_guid, raw=json_entry,
                          visible=True, last_published=last_publication)

        try:
            new_entry.save()
            return True
        except IntegrityError, e:
            pass

    except KeyboardInterrupt:
        raise
    except Exception as e:
        log.error('General Error on %s: %s', feed.url, e)
        log.exception(e)
