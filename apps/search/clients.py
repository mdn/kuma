import logging
import socket
import os

from django.conf import settings
from django.utils.encoding import smart_unicode

import bleach

from search import sphinxapi


log = logging.getLogger('k.search')


class SearchError(Exception):
    """An error occurred executing a search."""


class SearchClient(object):
    """
    Base-class for search clients
    """

    match_mode = sphinxapi.SPH_MATCH_EXTENDED2
    rank_mode = sphinxapi.SPH_RANK_PROXIMITY_BM25
    sort_mode = (sphinxapi.SPH_SORT_RELEVANCE, '')

    def __init__(self):
        self.sphinx = sphinxapi.SphinxClient()
        if os.environ.get('DJANGO_ENVIRONMENT') == 'test':
            self.sphinx.SetServer(settings.SPHINX_HOST,
                                  settings.TEST_SPHINX_PORT)
        else:
            self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)

        self.sphinx.SetMatchMode(self.match_mode)
        self.sphinx.SetRankingMode(self.rank_mode)
        self.sphinx.SetSortMode(*self.sort_mode)

    def _prepare_filters(self, filters=None):
        """Process filters and filter ranges."""
        sc = self.sphinx
        sc.ResetFilters()
        if filters is None:
            filters = []

        for f in filters:
            if f.get('range', False):
                sc.SetFilterRange(f['filter'], f['min'],
                                  f['max'], f.get('exclude', False))
            else:
                sc.SetFilter(f['filter'], f['value'],
                             f.get('exclude', False))

    def _prepare(self):
        """Override to twiddle `self.sphinx` before the query gets sent."""

    def _sanitize_query(self, query):
        """Strip control characters that cause problems."""
        return query.replace('^', '').replace('$', '')

    def _query_sphinx(self, query=''):
        """
        Pass the query to the SphinxClient() and return the results.

        Catches common exceptions raised by Sphinx.
        """

        query = self._sanitize_query(query)

        try:
            result = self.sphinx.Query(query, self.index)
        except socket.timeout:
            log.error('Query has timed out!')
            raise SearchError('Query has timed out!')
        except socket.error, msg:
            log.error('Query socket error: %s' % msg)
            raise SearchError('Could not execute your search!')
        except Exception, e:
            log.error('Sphinx threw an unknown exception: %s' % e)
            raise SearchError('Sphinx threw an unknown exception!')

        if result:
            return result['matches']
        else:
            return []

    def query(self, query, filters=None, offset=0,
              limit=settings.SEARCH_MAX_RESULTS):
        """Query the search index."""
        self._prepare_filters(filters)

        self.sphinx.SetFieldWeights(self.weights)
        self.sphinx.SetLimits(offset, limit)

        self._prepare()
        return self._query_sphinx(query)

    def excerpt(self, result, query):
        """
        Given document content and a search query (both strings), uses
        Sphinx to build an excerpt, highlighting the keywords from the
        query.

        Length of the final excerpt is roughly determined by
        SEARCH_SUMMARY_LENGTH in settings.py.
        """
        if not isinstance(result, basestring):
            return ''
        documents = [result]

        try:
            # build excerpts that are longer and truncate
            # see multiplier constant definition for details
            excerpt = self.sphinx.BuildExcerpts(
                documents, self.index, query,
                {'limit': settings.SEARCH_SUMMARY_LENGTH})[0]
        except socket.error:
            log.error('Socket error building excerpt!')
            excerpt = ''
        except socket.timeout:
            log.error('Building excerpt timed out!')
            excerpt = ''

        return bleach.clean(smart_unicode(excerpt))

    def set_sort_mode(self, mode, clause=''):
        self.sphinx.SetSortMode(mode, clause)


class QuestionsClient(SearchClient):
    index = 'questions'
    weights = {'title': 4, 'question_content': 3, 'answer_content': 3}
    groupsort = '@group desc'

    def _prepare(self):
        """Prepare to group the answers together."""
        super(QuestionsClient, self)._prepare()
        self.sphinx.SetGroupBy('question_id', sphinxapi.SPH_GROUPBY_ATTR,
                      self.groupsort)


class WikiClient(SearchClient):
    """
    Search the knowledge base
    """
    index = 'wiki_pages'
    weights = {'title': 6, 'content': 1, 'keywords': 4, 'summary': 2}


class DiscussionClient(SearchClient):
    """
    Search the discussion forums.
    """
    index = 'discussion_forums'
    weights = {'title': 2, 'content': 1}
    groupsort = '@group desc'
    sort_mode = (sphinxapi.SPH_SORT_ATTR_ASC, 'created')

    def _prepare(self):
        """Group posts together, and ensure thread['attrs']['updated'] is the
        last post's updated date.

        """
        super(DiscussionClient, self)._prepare()
        self.sphinx.SetGroupBy('thread_id', sphinxapi.SPH_GROUPBY_ATTR,
                               self.groupsort)
        self.sphinx.SetSortMode(*self.sort_mode)
