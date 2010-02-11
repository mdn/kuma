from django import test

from nose.tools import eq_

from sumo.models import ForumThread, WikiPage


class TestForumModel(test.TestCase):
    fixtures = ['threads.json']

    def test_get_url(self):
        f = ForumThread.objects.create(pk=12345,object=1)
        eq_(f.get_url(), '/en/forum/1/12345')


class TestWikiPage(test.TestCase):
    fixtures = ['pages.json']

    def test_get_url(self):
        w = WikiPage.objects.create(pk=1, lang='en', pageName='My Test Page')
        eq_(w.get_url(), '/en/kb/My Test Page')
