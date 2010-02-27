from django.conf import settings

from .sphinxapi import SphinxClient

import re

class SearchClient(object):
    """
    Base-class for search clients
    """

    def __init__(self):
        self.sphinx = SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)
        self.sphinx.SetLimits(0, settings.SEARCH_MAX_RESULTS)

    def query(self, query, filters): abstract

    def excerpt(self, results, query):
        """
        Returns a list of Sphinx excerpts for the passed-in list of results.

        Takes in a list of strings
        """
        documents = []
        for result in results:
            documents.append(results.data)

        return self.sphinx.BuildExcerpts(documents, self.index, query)


class ForumClient(SearchClient):
    """
    Search the forum
    """

    def query(self, query, filters=None):
        """
        Search through forum threads
        """

        if filters is None:
            filters = []

        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights({'title': 4, 'content': 3})

        for f in filters:
            if f.get('range', False):
                sc.SetFilterRange(f['filter'], f['min'],
                                  f['max'], f.get('exclude', False))
            else:
                sc.SetFilter(f['filter'], f['value'],
                             f.get('exclude', False))


        result = sc.Query(query, 'forum_threads')

        if result:
            return result['matches']
        else:
            return []


class WikiClient(SearchClient):
    """
    Search the knowledge base
    """
    index = 'wiki_pages'
    patterns = (
        (r'^!+',),
        (r'^;:',),
        (r'\n|\r',),
        (r'\{maketoc\}',),
        ('#\{ANAME.*?ANAME\}#',),
"""
        ('/__/'),
        ('/\^(.*?)\^/',),
        (r'{[a-zA-Z]+.*?}',),
        ('#~/?np~#',),
        ('/~(h|t)c~.*\~\/\1c~/U',),
        ('/\(\((.*)(?:\|(.*))?\)\)/Ue',),
        ('#\[.+\|(.+)\]#U','$1',),
        ('#\'\'#',),
        (r'%{2,}',),
"""
    )
    compiled_patterns = []

    def __init__(self):
        SearchClient.__init__(self)
        for pattern in self.patterns:
            self.compiled_patterns.append(re.compile(pattern[0], re.MULTILINE))

    def query(self, query, filters=None):
        """
        Search through the wiki (ie KB)
        """

        if filters is None:
            filters = []

        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights({'title': 4, 'keywords': 3})

        for f in filters:
            if f.get('range', False):
                sc.SetFilterRange(f['filter'], f['min'],
                                  f['max'], f.get('exclude', False))
            else:
                sc.SetFilter(f['filter'], f['value'],
                             f.get('exclude', False))

        result = sc.Query(query, self.index)

        if result:
            return result['matches']
        else:
            return []

    def excerpt(self, results, query):
        """
        Returns a list of wiki page excerpts for the passed-in list of results.

        Takes in a list of strings
        """
        documents = []
        for result in results:
            documents.append(result.data)

        raw_excerpts = self.sphinx.BuildExcerpts(documents, self.index, query)
        excerpts = []
        for raw_excerpt in raw_excerpts:
            excerpt = raw_excerpt
            for p in self.compiled_patterns:
                excerpt = p.sub(' ', excerpt)

            excerpts.append(excerpt)

        return excerpts
