from nose.tools import eq_

from django import test

import jingo

from sumo.models import ForumThread, WikiPage, Forum, TikiUser
from sumo import backends


def setup():
    jingo.load_helpers()
    test.Client().get('/')


class TestForumThreadModel(test.TestCase):
    fixtures = ['threads.json']

    def test_get_url(self):
        f = ForumThread.objects.create(pk=12345, object=1)
        eq_(f.get_url(), '/en-US/forum/1/12345')


class TestWikiPage(test.TestCase):
    fixtures = ['pages.json']

    def test_get_url(self):
        w = WikiPage.objects.create(pk=1, lang='en', pageName='My Test Page')
        eq_(w.get_url(), '/en-US/kb/My+Test+Page')

    def test_get_create_url(self):
        """Create url for a page that does not exist."""
        eq_('/tiki-editpage.php?page=Article+List',
            WikiPage.get_create_url('Article List'))

    def test_get_edit_url(self):
        """Edit url for a page exists."""
        w = WikiPage.objects.get(pageName='Installing Firefox')
        eq_('/tiki-editpage.php?page=Installing+Firefox', w.get_edit_url())


class TestForumModel(test.TestCase):
    fixtures = ['forums.json']

    def test_sanity(self):
        f = Forum.objects.create(pk=12, name='My Test Forum')
        eq_(f.get_url(), '/en-US/forum/12')


class TestTikiUserModel(test.TestCase):

    def test_django_user(self):
        tiki_user = TikiUser.objects.create(pk=1234, login='djangotestuser',
                                            email='user1234@nowhere',
                                            registrationDate=1207303253)
        user = backends.create_django_user(tiki_user)
        eq_(tiki_user.userId, user.id)
