from django.test import TestCase, client
from django.contrib.auth.models import User

from nose.tools import eq_

from sumo.urlresolvers import reverse


get = lambda c, v, **kw: c.get(reverse(v, **kw), follow=True)
post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


class TestCaseBase(TestCase):
    """Base TestCase for the Questions app test cases."""
    fixtures = ['users.json'] # TODO: , 'questions.json']

    def setUp(self):
        """Setup"""
        self.client = client.Client()
        self.client.get('/')
