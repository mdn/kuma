import logging
import socket

from django.conf import settings

from .sphinxapi import SphinxClient

import re

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

    def __init__(self):
        self.sphinx = SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)
        self.sphinx.SetLimits(0, settings.SEARCH_MAX_RESULTS)

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

    def query(self, query, filters=None):
        """
        Query the search index.
        """

        if filters is None:
            filters = []

        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights(self.weights)

        for f in filters:
            if f.get('range', False):
                sc.SetFilterRange(f['filter'], f['min'],
                                  f['max'], f.get('exclude', False))
            else:
                sc.SetFilter(f['filter'], f['value'],
                             f.get('exclude', False))


        try:
            result = sc.Query(query, self.index)
        except socket.timeout:
            log.error("Query has timed out!")
            raise SearchError("Query has timed out!")
        except socket.error, msg:
            log.error("Query socket error: %s" % msg)
            raise SearchError("Could not execute your search!")
        except Exception, e:
            log.error("Sphinx threw an unknown exception: %s" % e)
            raise SearchError("Sphinx threw an unknown exception!")

        if result:
            return result['matches']
        else:
            return []

    def excerpt(self, result, query):
        """
        Returns an excerpt for the passed-in string

        Takes in a string
        """
        documents = [result]

        # build excerpts that are longer and truncate
        # see multiplier constant definition for details
        raw_excerpt = self.sphinx.BuildExcerpts(documents, self.index, query,
            {'limit': settings.SEARCH_SUMMARY_LENGTH
                * settings.SEARCH_SUMMARY_LENGTH_MULTIPLIER})[0]

        excerpt = raw_excerpt
        for p in self.compiled_patterns:
            excerpt = p[0].sub(p[1], excerpt)

        # truncate long excerpts
        if len(excerpt) > settings.SEARCH_SUMMARY_LENGTH:
            excerpt = excerpt[:settings.SEARCH_SUMMARY_LENGTH] \
                + self.truncate_pattern.sub('',
                    excerpt[settings.SEARCH_SUMMARY_LENGTH:])
            if excerpt[-1] != '.':
                excerpt += '...'

        return excerpt

    def set_sort_mode(self, mode, clause=''):
        self.sphinx.SetSortMode(mode, clause)


class ForumClient(SearchClient):
    """
    Search the forum
    """
    index = 'forum_threads'
    weights = {'title': 4, 'content': 3}


class WikiClient(SearchClient):
    """
    Search the knowledge base
    """
    index = 'wiki_pages'
    weights = {'title': 4, 'content': 3}
