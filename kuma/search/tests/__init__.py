from __future__ import absolute_import
import time

from django.conf import settings

from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import ConnectionError, NotFoundError
from rest_framework.test import APIRequestFactory

from kuma.core.tests import LocalizingMixin
from kuma.core.urlresolvers import reset_url_prefixer
from kuma.core.middleware import LocaleURLMiddleware
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
        # TODO: cleanup after upgarding test-utils (also in tearDownClass)
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
            # TODO: cleanup after upgarding test-utils
            settings.ES_LIVE_INDEX = cls._old_es_live_index

    def setUp(self):
        super(ElasticTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ElasticTestCase, self).tearDown()
        self.teardown_indexes()
        reset_url_prefixer()

    def refresh(self, timesleep=0):
        index = Index.objects.get_current().prefixed_name
        # Any time we're doing a refresh, we're making sure that the
        # index is ready to be queried.  Given that, it's almost
        # always the case that we want to run all the generated tasks,
        # then refresh.
        connections.get_connection().indices.refresh(index=index)
        if timesleep > 0:
            time.sleep(timesleep)

    def setup_indexes(self, wait=True):
        """(Re-)create ES indexes."""
        # Removes the index, creates a new one, and indexes
        # existing data into it.
        WikiDocumentType.reindex_all()

        self.refresh()
        if wait:
            connections.get_connection().cluster.health(wait_for_status='yellow')

    def teardown_indexes(self):
        es = connections.get_connection()
        for index in Index.objects.all():
            try:
                es.indices.delete(index.prefixed_name)
            except NotFoundError:
                # If we get this error, it means the index didn't exist
                # so there's nothing to delete.
                pass

    def get_request(self, *args, **kwargs):
        request = factory.get(*args, **kwargs)
        # setting request.locale correctly
        LocaleURLMiddleware().process_request(request)
        return request
