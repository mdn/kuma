from nose.tools import ok_, eq_

from elasticsearch_dsl import query

from kuma.wiki.models import Document
from kuma.wiki.search import WikiDocumentType

from . import ElasticTestCase


class WikiDocumentTypeTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ['wiki/documents.json']

    def test_get_excerpt_strips_html(self):
        self.refresh()
        results = WikiDocumentType.search().query('match', content='audio')
        ok_(results.count() > 0)
        for doc in results.execute():
            excerpt = doc.get_excerpt()
            ok_('audio' in excerpt)
            ok_('<strong>' not in excerpt)

    def test_current_locale_results(self):
        self.refresh()
        results = (WikiDocumentType.search()
                                   .query(query.Match(title='article') |
                                          query.Match(content='article'))
                                   .filter('term', locale='en-US'))
        for doc in results.execute():
            eq_('en-US', doc.locale)

    def test_get_excerpt_uses_summary(self):
        self.refresh()
        results = WikiDocumentType.search().query('match', content='audio')
        ok_(results.count() > 0)
        for doc in results.execute():
            excerpt = doc.get_excerpt()
            ok_('the word for tough things' in excerpt)
            ok_('extra content' not in excerpt)

    def test_hidden_slugs_get_indexable(self):
        self.refresh()
        title_list = WikiDocumentType.get_indexable().values_list('title',
                                                                  flat=True)
        ok_('User:jezdez' not in title_list)

    def test_hidden_slugs_should_update(self):
        jezdez_doc = Document.objects.get(slug='User:jezdez')
        eq_(WikiDocumentType.should_update(jezdez_doc), False)
