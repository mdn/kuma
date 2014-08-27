from nose.tools import ok_, eq_

from kuma.wiki.models import Document
from search.models import DocumentType
from search.tests import ElasticTestCase


class DocumentTypeTests(ElasticTestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def test_get_excerpt_strips_html(self):
        self.refresh()
        results = (DocumentType.search().query(content__match='audio')
                                        .highlight('content'))
        ok_(results.count() > 0)
        for doc in results:
            excerpt = doc.get_excerpt()
            ok_('audio' in excerpt)
            ok_('<strong>' not in excerpt)

    def test_get_excerpt_without_highlight_match(self):
        self.refresh()
        results = (DocumentType.search().query(or_={'title': 'lorem',
                                                    'content': 'lorem'})
                                        .highlight('content'))

        ok_(results.count() > 0)
        for doc in results:
            excerpt = doc.get_excerpt()
            eq_('audio is in this but the word for tough things'
                ' will be ignored', excerpt)

    def test_current_locale_results(self):
        self.refresh()
        results = (DocumentType.search().query(or_={'title': 'article',
                                                    'content': 'article'})
                                        .filter(locale='en-US')
                                        .highlight('content'))
        for doc in results:
            eq_('en-US', doc.locale)

    def test_get_excerpt_uses_summary(self):
        self.refresh()
        results = (DocumentType.search().query(content__match='audio')
                                        .highlight('content'))
        ok_(results.count() > 0)
        for doc in results:
            excerpt = doc.get_excerpt()
            ok_('the word for tough things' in excerpt)
            ok_('extra content' not in excerpt)

    def test_hidden_slugs_get_indexable(self):
        self.refresh()
        title_list = DocumentType.get_indexable().values_list('title',
                                                              flat=True)
        ok_('User:jezdez' not in title_list)

    def test_hidden_slugs_should_update(self):
        jezdez_doc = Document.objects.get(slug='User:jezdez')
        eq_(DocumentType.should_update(jezdez_doc), False)
