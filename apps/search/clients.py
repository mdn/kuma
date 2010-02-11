from django.conf import settings

from .sphinxapi import SphinxClient


class SearchClient(object):
    """
    Base-class for search clients
    """

    def __init__(self):
        self.sphinx = SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)
        self.sphinx.SetLimits(0, 1000)

    def query(self, query, filters): abstract


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

        result = sc.Query(query, 'wiki_pages')

        if result:
            return result['matches']
        else:
            return []
