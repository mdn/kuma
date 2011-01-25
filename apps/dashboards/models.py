import json
import logging
from urllib2 import HTTPBasicAuthHandler, build_opener

from django.conf import settings
from django.db import models

from tower import ugettext_lazy as _lazy

from sumo.models import ModelBase
from wiki.models import Document


log = logging.getLogger('k.dashboards')

# Report time period enumerations:
THIS_WEEK = 0
ALL_TIME = 1
PERIODS = [(THIS_WEEK, _lazy(u'This Week')),
           (ALL_TIME, _lazy(u'All Time'))]


class StatsException(Exception):
    """An error in the stats returned by the third-party analytics package"""
    def __init__(self, msg):
        self.msg = msg


class StatsIOError(IOError):
    """An error communicating with WebTrends"""


def period_dates():
    """Return when each period begins and ends, relative to now.

    Return values are in the format WebTrends likes: "2010m01d30" or
    "current_day-7".

    """
    # WebTrends' server apparently runs in UTC, FWIW.
    yesterday = 'current_day-1'  # Start at yesterday so we get a full week of
                                 # data.
    return {THIS_WEEK: ('current_day-7',
                        yesterday),
            ALL_TIME: (settings.WEBTRENDS_EPOCH.strftime('%Ym%md%d'),
                       yesterday)}


class WikiDocumentVisits(ModelBase):
    """Web stats for Knowledge Base Documents"""

    document = models.ForeignKey(Document)
    visits = models.IntegerField(db_index=True)
    period = models.IntegerField(choices=PERIODS)  # indexed by unique_together

    class Meta(object):
        unique_together = ('period', 'document')

    @classmethod
    def reload_period_from_json(cls, period, json_data):
        """Replace the stats for the given period with the given JSON."""
        counts = cls._visit_counts(json_data)
        if counts:
            # Delete and remake the rows:
            # Horribly inefficient until
            # http://code.djangoproject.com/ticket/9519 is fixed.
            cls.objects.filter(period=period).delete()
            for doc_id, visits in counts.iteritems():
                cls.objects.create(document=Document(pk=doc_id), visits=visits,
                                   period=period)
        else:
            # Don't erase interesting data if there's nothing to replace it:
            log.warning('WebTrends returned no interesting data, so I kept '
                        'what I had.')

    @classmethod
    def _visit_counts(cls, json_data):
        """Given WebTrends JSON data, return a dict of doc IDs and visits:

            {document ID: number of visits, ...}

        If there is no interesting data in the given JSON, return {}.

        """
        # We're very defensive here, as WebTrends has been known to return
        # invalid garbage of various sorts.
        try:
            data = json.loads(json_data)['data']
        except (ValueError, KeyError, TypeError):
            raise StatsException('Error extracting data from WebTrends JSON')

        try:
            pages = (data[data.keys()[0]]['SubRows'] if data.keys()
                     else {}).iteritems()
        except (AttributeError, IndexError, KeyError, TypeError):
            raise StatsException('Error extracting pages from WebTrends data')

        counts = {}
        for url, page_info in pages:
            doc = Document.from_url(url,
                required_locale=settings.LANGUAGE_CODE, id_only=True)
            if not doc:
                continue

            # Get visit count:
            try:
                visits = int(page_info['measures']['Visits'])
            except (ValueError, KeyError, TypeError):
                continue

            # Sometimes WebTrends repeats a URL modulo a space, etc. These can
            # resolve to the same document. An arbitrary one wins.
            # TODO: Should we be summing these?
            if doc.pk in counts:
                log.info('WebTrends has the following duplicate URL for this '
                         'document: %s' % url)
            counts[doc.pk] = visits
        return counts

    @classmethod
    def json_for(cls, period):
        """Return the JSON-formatted WebTrends stats for the given period.

        Make one attempt to fetch and reload the data. If something fails, it's
        the caller's responsibility to retry.

        """
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(realm=settings.WEBTRENDS_REALM,
                                  uri=settings.WEBTRENDS_WIKI_REPORT_URL,
                                  user=settings.WEBTRENDS_USER,
                                  passwd=settings.WEBTRENDS_PASSWORD)
        opener = build_opener(auth_handler)
        start, end = period_dates()[period]
        url = (settings.WEBTRENDS_WIKI_REPORT_URL +
               '&start_period=%s&end_period=%s' % (start, end))
        try:
            # TODO: A wrong username or password results in a recursion depth
            # error.
            return opener.open(url).read()
        except IOError, e:
            raise StatsIOError(*e.args)
