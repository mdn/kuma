from elasticsearch_dsl import query

from kuma.wiki.search import WikiDocumentType

from . import ElasticTestCase


class WikiDocumentTypeTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ["wiki/documents.json"]

    def test_get_excerpt_strips_html(self):
        self.refresh()
        results = WikiDocumentType.search().query("match", content="audio")
        assert results.count()
        for doc in results.execute():
            excerpt = doc.get_excerpt()
            assert "audio" in excerpt
            assert "<strong>" not in excerpt

    def test_current_locale_results(self):
        self.refresh()
        results = (
            WikiDocumentType.search()
            .query(query.Match(title="article") | query.Match(content="article"))
            .filter("term", locale="en-US")
        )
        for doc in results.execute():
            assert "en-US" == doc.locale

    def test_get_excerpt_uses_summary(self):
        self.refresh()
        results = WikiDocumentType.search().query("match", content="audio")
        assert results.count()
        for doc in results.execute():
            excerpt = doc.get_excerpt()
            assert "the word for tough things" in excerpt
            assert "extra content" not in excerpt

    def test_hidden_slugs_get_indexable(self):
        self.refresh()
        title_list = WikiDocumentType.get_indexable().values_list("title", flat=True)
        assert "User:jezdez" not in title_list
