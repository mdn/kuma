from datetime import datetime

from django.test import TestCase, client
from django.conf import settings
from django.template.defaultfilters import slugify


class TestCaseBase(TestCase):
    """Base TestCase for the flagit app test cases."""

    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        """Setup"""
        self.client = client.Client()
        self.client.get('/')

        # Change the CACHE_PREFIX to avoid conflicts
        self.orig_cache_prefix = getattr(settings, 'CACHE_PREFIX', None)
        settings.CACHE_PREFIX = self.orig_cache_prefix or '' + 'test' + \
                                slugify(datetime.now())

    def tearDown(self):
        settings.CACHE_PREFIX = self.orig_cache_prefix
