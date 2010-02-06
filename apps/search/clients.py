from .sphinxapi import SphinxClient
from django.conf import settings
from .utils import crc32

class SearchClient(object):
    """
    Base-class for search clients
    """

    def __init__(self):
        self.sphinx = SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST,settings.SPHINX_PORT)

class ForumClient(SearchClient):
    """
    Search the forum
    """

    def query(self, query, **kwargs):
        """
        Search through forum threads
        """

        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights({'title':4,'content':3})

        

        result = sc.Query(query,'forum_threads')
        if result:
            return result['matches']
        else:
            return []


class WikiClient(SearchClient):
    """
    Search the knowledge base
    """

    def query(self,query,locale='en',filters={}):
        """
        Search through the wiki (ie KB)
        """

        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights({'title':4,'keywords':3})

        if not filters.get('category',0):
            filters['category'] = (1,17,18,)
        if not filters.get('locale',0):
            filters['locale'] = (crc32(locale),)

        for k in filters:
            if filters[k]:
                sc.SetFilter(k,filters[k])

        result = sc.Query(query,'wiki_pages')
        if result:
            return result['matches']
        else:
            return []

