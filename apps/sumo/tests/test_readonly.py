import copy

from django.conf import settings
from django.db import models
from django.utils import importlib

import test_utils
from nose.tools import assert_raises, eq_
from pyquery import PyQuery as pq

from devmo import get_mysql_error
from questions.models import Question
from sumo.urlresolvers import reverse


# Django compatibility shim. Once we're on Django 1.4, do:
# from django.db.utils import DatabaseError
DatabaseError = get_mysql_error()


class ReadOnlyModeTest(test_utils.TestCase):
    extra = ('sumo.middleware.ReadOnlyMiddleware',)

    def setUp(self):
        models.signals.pre_save.connect(self.db_error)
        models.signals.pre_delete.connect(self.db_error)
        self.old_settings = copy.deepcopy(settings._wrapped.__dict__)
        settings_module = importlib.import_module(settings.SETTINGS_MODULE)
        settings_module.read_only_mode(settings._wrapped.__dict__)
        self.client.handler.load_middleware()

    def tearDown(self):
        settings._wrapped.__dict__ = self.old_settings
        models.signals.pre_save.disconnect(self.db_error)
        models.signals.pre_delete.disconnect(self.db_error)

    def db_error(self, *args, **kwargs):
        raise DatabaseError("You can't do this in read-only mode.")

    def test_db_error(self):
        assert_raises(DatabaseError, Question.objects.create, id=12)

    def test_login_error(self):
        # This tries to do a db write.
        r = self.client.get(reverse('account_login'))
        eq_(r.status_code, 503)
        title = pq(r.content)('title').text()
        assert title.startswith('Maintenance in progress'), title

    def test_bail_on_post(self):
        r = self.client.post('/en-US/questions')
        eq_(r.status_code, 503)
        title = pq(r.content)('title').text()
        assert title.startswith('Maintenance in progress'), title
