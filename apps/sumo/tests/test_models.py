from django import test

from nose.tools import eq_

from sumo.models import ForumThread, WikiPage, Forum


class TestForumThreadModel(test.TestCase):
    fixtures = ['threads.json']

    def test_get_url(self):
        f = ForumThread.objects.create(pk=12345, object=1)
        eq_(f.get_url(), '/en/forum/1/12345')


class TestWikiPage(test.TestCase):
    fixtures = ['pages.json']

    def test_get_url(self):
        w = WikiPage.objects.create(pk=1, lang='en', pageName='My Test Page')
        eq_(w.get_url(), '/en/kb/My+Test+Page')


class TestForumModel(test.TestCase):
    fixtures = ['forums.json']

    def test_sanity(self):
        f = Forum.objects.create(pk=12, name='My Test Forum')
        eq_(f.get_url(), '/en/forum/12')

