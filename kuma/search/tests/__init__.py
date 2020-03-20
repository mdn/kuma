from django.conf import settings
from elasticsearch.exceptions import ConnectionError
from elasticsearch_dsl.connections import connections
from rest_framework.test import APIRequestFactory

from kuma.core.i18n import activate_language_from_request
from kuma.users.tests import UserTestCase
from kuma.wiki.search import WikiDocumentType

from ..models import Index


factory = APIRequestFactory()


class ElasticTestCase(UserTestCase):
    """Base class for Elastic Search tests, providing some conveniences"""

    @classmethod
    def setUpClass(cls):
        super(ElasticTestCase, cls).setUpClass()

        if not getattr(settings, "ES_URLS", None):
            cls.skipme = True
            return

        try:
            connections.get_connection().cluster.health()
        except ConnectionError:
            cls.skipme = True
            return

        cls._old_es_index_prefix = settings.ES_INDEX_PREFIX
        settings.ES_INDEX_PREFIX = "test-%s" % settings.ES_INDEX_PREFIX
        cls._old_es_live_index = settings.ES_LIVE_INDEX
        settings.ES_LIVE_INDEX = True

    @classmethod
    def tearDownClass(cls):
        super(ElasticTestCase, cls).tearDownClass()

        if not cls.skipme:
            # Restore old setting.
            settings.ES_INDEX_PREFIX = cls._old_es_index_prefix
            settings.ES_LIVE_INDEX = cls._old_es_live_index

    def setUp(self):
        super(ElasticTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ElasticTestCase, self).tearDown()
        self.teardown_indexes()

    def refresh(self, index=None):
        index = index or Index.objects.get_current().prefixed_name
        # Any time we're doing a refresh, we're making sure that the
        # index is ready to be queried.  Given that, it's almost
        # always the case that we want to run all the generated tasks,
        # then refresh.
        connections.get_connection().indices.refresh(index=index)

    def setup_indexes(self):
        """Clear and repopulate the current index."""
        WikiDocumentType.reindex_all()

    def teardown_indexes(self):
        es = connections.get_connection()
        for index in Index.objects.all():
            # Ignore indices that do not exist.
            es.indices.delete(index.prefixed_name, ignore=[404])

    def get_request(self, *args, **kwargs):
        request = factory.get(*args, **kwargs)
        # setting request.LANGUAGE_CODE correctly
        activate_language_from_request(request)
        return request
