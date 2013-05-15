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
