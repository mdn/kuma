from .sphinxapi import SphinxClient
from django.conf import settings
from .utils import crc32

class Client(object):
    """
    Executes searches against the Sphinx client
    """

    def __init__(self):
        self.sphinx = SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST,settings.SPHINX_PORT)

    def search_forum(self, query, filters={'forumId':(1,),}):
        """
        Search through forum threads
        """

        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights({'title':4,'content':3})

        for k in filters:
            sc.SetFilter(k,filters[k])

        result = sc.Query(query,'forum_threads')
        if result:
            return result['matches']
        else:
            return []

    def search_wiki(self,query,locale='en',filters={}):
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

