import datetime
from optparse import make_option
import socket
import time

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import IntegrityError
from django.utils import encoding, hashcompat

import commonware
import feedparser
import jsonpickle

from feeder.models import Feed, Entry
from utils import locked


log = commonware.log.getLogger('mdn.feeder')


class Command(NoArgsCommand):
    """Update all registered RSS/Atom feeds."""

    option_list = NoArgsCommand.option_list + (
        make_option('--force', '-f', dest='force', action='store_true',
                    default=False, help='Fetch even disabled feeds.'),
    )

    @locked('kuma_feeder_lock')
    def handle_noargs(self, **options):
        """
        Locked command handler to avoid running this command more than once
        simultaneously.
        """
        log.info("Starting to fetch updated feeds")
        start = time.time()
        socket.setdefaulttimeout(settings.FEEDER_TIMEOUT)

        feeds = Feed.objects.all()
        if not options.get('force', False):
            feeds = feeds.filter()
        else:
            log.info('--force option set: Trying to fetch all known feeds.')

        new_entry_count = 0
        for feed in feeds:
            new_entry_count += self.update_feed(feed, **options)

        log.info("Finished run in %f seconds for %d new entries" % (
            (time.time() - start), new_entry_count))

    def update_feed(self, feed, **options):
        """
        Update a single feed.

        Returns number of newly fetched entries.
        """

        new_entry_count = 0

        try:
            stream = self.fetch_feed(feed)

            if stream:
                log.debug('Processing %s: %s' % (feed.shortname, feed.url))

                if 'feed' in stream and 'title' in stream.feed:
                    log.debug('Processing title: %s', stream.feed.title)

                dirty_feed = False
                if 'feed' in stream and 'title' in stream.feed and feed.title != stream.feed.title:
                    feed.title = stream.feed.title
                    dirty_feed = True
                else:
                    if (not 'feed' in stream) or (not 'title' in stream.feed):
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
                    if self.save_entry(feed, entry):
                        new_entry_count += 1

                # Remove old entries if applicable.
                feed.delete_old_entries()

        except KeyboardInterrupt:
            raise
        except Exception, e:
            log.error("General Error starting loop: %s", e)
            log.exception(e)

        return new_entry_count

    def fetch_feed(self, feed):
        """
        Fetch a feed from its URL and update its metadata if necessary.

        Returns stream if feed had updates, None otherwise.
        """
        dirty_feed = False
        has_updates = False

        if feed.etag == None:
            feed.etag = ''
        if feed.last_modified == None:
            feed.last_modified = datetime.datetime(1975, 1, 10)
        log.debug("feed id=%s feed url=%s etag=%s last_modified=%s" % (
            feed.shortname, feed.url, feed.etag, str(feed.last_modified)))
        stream = feedparser.parse(feed.url, etag=feed.etag,
                                  modified=feed.last_modified.timetuple())

        # Next 70 lines of code from planet/planet/.__init__.py channel update
        url_status = str(500)
        if stream.has_key("status"):
            url_status = str(stream.status)
        elif stream.has_key("entries") and len(stream.entries)>0:
            url_status = str(200)
        elif stream.bozo and stream.bozo_exception.__class__.__name__=='Timeout':
            url_status = str(408)

        if url_status == '301' and \
            (stream.has_key("entries") and len(stream.entries)>0):
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
            feed.disabled_reason = "This is not a feed or it's been removed removed!";
            dirty_feed = True
        elif url_status == '410':
            log.info("Feed %s gone", feed.url)
            feed.enabled = False
            feed.disabled_reason = "This feed has been removed!";
            dirty_feed = True
        elif url_status == '408':
            feed.enabled = False
            feed.disabled_reason = "This feed didn't respond after %d seconds" % settings.FEEDER_TIMEOUT
            dirty_feed = True
        elif int(url_status) >= 400:
            feed.enabled = False
            bozo_msg = ""
            if 1 == stream.bozo and 'bozo_exception' in stream.keys():
                log.error('Unable to fetch %s Exception: %s',
                      feed.url, stream.bozo_exception)
                bozo_msg = stream.bozo_exception
            feed.disabled_reason = "Error while reading the feed: %s __ %s" % (url_status, bozo_msg)
            dirty_feed = True
        else:
            # We've got a live one...
            if not feed.enabled or feed.disabled_reason:
                # Reset disabled status.
                feed.enabled = True
                feed.disabled_reason = ''
                dirty_feed = True
            has_updates = True

        if stream.has_key("etag") and stream.etag != feed.etag and stream.etag != None:
            log.info("New etag %s" % stream.etag)
            feed.etag = stream.etag
            dirty_feed = True

        if stream.has_key("modified") and stream.modified != feed.last_modified:
            feed.last_modified = time.strftime("%Y-%m-%d %H:%M:%S", stream.modified)
            log.info("New last_modified %s" % feed.last_modified)
            dirty_feed = True

        if dirty_feed:
            try:
                dirty_feed = False
                log.debug("Feed changed, updating db" % feed)
                feed.save()
            except KeyboardInterrupt:
                raise
            except Exception, x:
                log.error("Unable to update feed")
                log.exception(x)

        return has_updates and stream or None

    def save_entry(self, feed, entry):
        """Save a new entry to the database."""
        try:
            json_entry = jsonpickle.encode(entry)
            entry_guid = ''

            if ('guid' in entry and
                len(entry.guid) <= Entry._meta.get_field_by_name('guid')[0].max_length):
                entry_guid = entry.guid
            else:
                entry_guid = hashcompat.md5_constructor(encoding.smart_str(
                    json_entry)).hexdigest()

            if 'updated_parsed' in entry:
                yr, mon, d, hr, min, sec = entry.updated_parsed[:-3]
                last_publication = datetime.datetime(yr, mon, d, hr, min, sec)
            else:
                log.warn("Entry has no updated field, faking it")
                last_publication = datetime.datetime.now()

            new_entry = Entry(feed=feed, guid=entry_guid, raw=json_entry,
                              visible=True, last_published=last_publication)

            try:
                new_entry.save()
                return True
            except IntegrityError, e:
                #log.debug('Skipping duplicate entry %s, caught error: %s', entry_guid, e)
                pass

        except KeyboardInterrupt:
            raise
        except Exception, e:
            log.error('General Error on %s: %s', feed.url, e)
            log.exception(e)
