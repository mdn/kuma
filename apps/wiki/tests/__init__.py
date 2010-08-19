from django.test import TestCase, client

from sumo.urlresolvers import reverse


get = lambda c, v, **kw: c.get(reverse(v, **kw), follow=True)
post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


class TestCaseBase(TestCase):
    """Base TestCase for the wiki app test cases."""

    fixtures = []

    def setUp(self):
        self.client = client.Client()
        self.client.get('/')

    def tearDown(self):
        pass
