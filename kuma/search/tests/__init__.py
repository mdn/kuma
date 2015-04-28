from __future__ import absolute_import

import time

from django.conf import settings

from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import ConnectionError
from rest_framework.test import APIRequestFactory

from kuma.core.middleware import LocaleURLMiddleware
from kuma.core.tests import LocalizingMixin
from kuma.core.urlresolvers import reset_url_prefixer
from kuma.users.tests import UserTestCase
from kuma.wiki.search import WikiDocumentType

from ..models import Index


class LocalizingAPIRequestFactory(LocalizingMixin, APIRequestFactory):
    pass

factory = LocalizingAPIRequestFactory()


class ElasticTestCase(UserTestCase):
    """Base class for Elastic Search tests, providing some conveniences"""

    @classmethod
    def setUpClass(cls):
        try:
            super(ElasticTestCase, cls).setUpClass()
        except AttributeError:
            # python 2.6 has no setUpClass, but that's okay
            pass

        if not getattr(settings, 'ES_URLS', None):
            cls.skipme = True
            return

        try:
            connections.get_connection().cluster.health()
        except ConnectionError:
            cls.skipme = True
            return

        cls._old_es_index_prefix = settings.ES_INDEX_PREFIX
        settings.ES_INDEX_PREFIX = 'test-%s' % settings.ES_INDEX_PREFIX
        cls._old_es_live_index = settings.ES_LIVE_INDEX
        settings.ES_LIVE_INDEX = True

    @classmethod
    def tearDownClass(cls):
        try:
            super(ElasticTestCase, cls).tearDownClass()
        except AttributeError:
            # python 2.6 has no tearDownClass, but that's okay
            pass

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
        reset_url_prefixer()

    def refresh(self, index=None, timesleep=0):
        index = index or Index.objects.get_current().prefixed_name
        # Any time we're doing a refresh, we're making sure that the
        # index is ready to be queried.  Given that, it's almost
        # always the case that we want to run all the generated tasks,
        # then refresh.
        connections.get_connection().indices.refresh(index=index)
        if timesleep > 0:
            time.sleep(timesleep)

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
        # setting request.locale correctly
        LocaleURLMiddleware().process_request(request)
        return request
