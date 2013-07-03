# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
