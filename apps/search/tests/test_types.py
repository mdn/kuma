from nose.tools import ok_, eq_

from search.tests import ElasticTestCase

from wiki.models import DocumentType


class DocumentTypeTests(ElasticTestCase):
    fixtures = ['wiki/documents.json']

    def test_get_excerpt_strips_html(self):
        self.refresh()
        results = (DocumentType.search().query(content__match='audio')
                                        .highlight('content'))
        ok_(results.count() > 0)
        for doc in results:
            excerpt = doc.get_excerpt()
            ok_('audio' in excerpt)
            ok_('<strong>' not in excerpt)

        results = (DocumentType.search().query(or_={'title': 'lorem',
                                                    'content': 'lorem'})
                                        .highlight('content'))
        ok_(results.count() > 0)
        for doc in results:
            excerpt = doc.get_excerpt()
            eq_('', excerpt)

    def test_current_locale_results(self):
        self.refresh()
        results = (DocumentType.search().query(or_={'title': 'article',
                                                    'content': 'article'})
                                        .filter(locale='en-US')
                                        .highlight('content'))
        for doc in results:
            eq_('en-US', doc.locale)