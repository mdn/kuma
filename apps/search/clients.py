import logging
import socket
import re

from django.conf import settings
from django.utils.encoding import smart_unicode

from bleach import Bleach

import search as constants
from .sphinxapi import SphinxClient

MARKUP_PATTERNS = (
    (r'^!+',),
    (r'^;:',),
    (r'^#',),
    (r'\n|\r',),
    (r'\{maketoc\}',),
    (r'\{ANAME.*?ANAME\}',),
    (r'\{[a-zA-Z]+.*?\}',),
    (r'\{.*?$',),
    (r'__',),
    (r'\'\'',),
    (r'%{2,}',),
    (r'\*|\^|;|/\}',),
    (r'~/?np~',),
    (r'~/?(h|t)c~',),
    (r'\(spans.*?\)',),
    (r'\}',),
    (r'\(\(.*?\|(?P<name>.*?)\)\)', '\g<name>'),
    (r'\(\((?P<name>.*?)\)\)', '\g<name>'),
    (r'\(\(',),
    (r'\)\)',),
    (r'\[.+?\|(?P<name>.+?)\]', '\g<name>'),
    (r'\[(?P<name>.+?)\]', '\g<name>'),
    (r'/wiki_up.*? ',),
    (r'&quot;',),
    (r'^!! Issue.+!! Description',),
    (r'\s+',),
)

log = logging.getLogger('k.search')


class SearchError(Exception):
    pass


class SearchClient(object):
    """
    Base-class for search clients
    """

    bleach = Bleach()

    def __init__(self):
        self.sphinx = SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)

        # initialize regexes for markup cleaning
        self.truncate_pattern = re.compile(r'\s.*', re.MULTILINE)
        self.compiled_patterns = []

        if MARKUP_PATTERNS:
            for pattern in MARKUP_PATTERNS:
                p = [re.compile(pattern[0], re.MULTILINE)]
                if len(pattern) > 1:
                    p.append(pattern[1])
                else:
                    p.append(' ')

                self.compiled_patterns.append(p)

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

    def _query_sphinx(self, query=''):
        """
        Pass the query to the SphinxClient() and return the results.

        Catches common exceptions raised by Sphinx.
        """
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
            raw_excerpt = self.sphinx.BuildExcerpts(
                documents, self.index, query,
                {'limit': settings.SEARCH_SUMMARY_LENGTH
                 * settings.SEARCH_SUMMARY_LENGTH_MULTIPLIER})[0]
        except socket.error:
            log.error('Socket error building excerpt!')
            raw_excerpt = ''
        except socket.timeout:
            log.error('Building excerpt timed out!')
            raw_excerpt = ''

        excerpt = smart_unicode(raw_excerpt)
        for p in self.compiled_patterns:
            excerpt = p[0].sub(p[1], excerpt)

        # truncate long excerpts
        if len(excerpt) > settings.SEARCH_SUMMARY_LENGTH:
            excerpt = excerpt[:settings.SEARCH_SUMMARY_LENGTH] \
                + self.truncate_pattern.sub('',
                    excerpt[settings.SEARCH_SUMMARY_LENGTH:])
            if not excerpt.endswith('.'):
                excerpt += u'...'

        return self.bleach.clean(excerpt)

    def set_sort_mode(self, mode, clause=''):
        self.sphinx.SetSortMode(mode, clause)


class QuestionsClient(SearchClient):
    index = 'questions'
    weights = {'title': 4, 'question_content': 3, 'answer_content': 3}

    def __init__(self):
        super(QuestionsClient, self).__init__()
        self.groupsort = '@group desc'

    def _prepare(self):
        """Prepare to group the answers together."""
        super(QuestionsClient, self)._prepare()
        self.sphinx.SetGroupBy('question_id', constants.SPH_GROUPBY_ATTR,
                      self.groupsort)

    def set_groupsort(self, groupsort=''):
        self.groupsort = groupsort


class WikiClient(SearchClient):
    """
    Search the knowledge base
    """
    index = 'wiki_pages'
    weights = {'title': 4, 'content': 1, 'keywords': 4, 'tag': 2, 'summary': 2}


class DiscussionClient(SearchClient):
    """
    Search the discussion forums.
    """
    index = 'discussion_forums'
    weights = {'title': 2, 'content': 1}

    def __init__(self):
        super(DiscussionClient, self).__init__()
        self.groupsort = '@group desc'

    def _prepare(self):
        """Group posts together, and ensure thread['attrs']['updated'] is the
        last post's updated date.

        """
        super(DiscussionClient, self)._prepare()
        self.sphinx.SetGroupBy('thread_id', constants.SPH_GROUPBY_ATTR,
                               self.groupsort)
        self.sphinx.SetSortMode(constants.SPH_SORT_ATTR_ASC, 'created')

    def set_groupsort(self, groupsort=''):
        self.groupsort = groupsort
