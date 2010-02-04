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

    """
    Search the forum data
    """
    def search_forum(self, query):
        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights({'title':4,'content':3})
        sc.SetFilter('forumId',(1,))

        result = sc.Query(query,'forum_threads')
        if result:
            return result['matches']
        else:
            return []

    """
    Search the wiki (knowledge base)
    """
    def search_wiki(self,query,locale='en'):
        sc = self.sphinx
        sc.ResetFilters()

        sc.SetFieldWeights({'title':4,'keywords':3})
        sc.SetFilter('category',(1,17,18,));
        sc.SetFilter('locale',(crc32(locale),))

        result = sc.Query(query,'wiki_pages')
        if result:
            return result['matches']
        else:
            return []

