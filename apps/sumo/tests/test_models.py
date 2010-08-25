from nose.tools import eq_

import jingo

from sumo import backends
from sumo.models import WikiPage, TikiUser
from sumo.tests import TestCase


def setup():
    jingo.load_helpers()


class TestWikiPage(TestCase):
    fixtures = ['pages.json']

    def test_get_url(self):
        w = WikiPage.objects.create(pk=1, lang='en', title='My Test Page')
        eq_(w.get_url(), '/en-US/kb/My+Test+Page')

    def test_get_create_url(self):
        """Create url for a page that does not exist."""
        eq_('/tiki-editpage.php?page=Article+List',
            WikiPage.get_create_url('Article List'))

    def test_get_edit_url(self):
        """Edit url for a page exists."""
        w = WikiPage.objects.get(title='Installing Firefox')
        eq_('/tiki-editpage.php?page=Installing+Firefox', w.get_edit_url())


class TestTikiUserModel(TestCase):

    def test_django_user(self):
        tiki_user = TikiUser.objects.create(pk=1234, login='djangotestuser',
                                            email='user1234@nowhere',
                                            registrationDate=1207303253)
        user = backends.create_django_user(tiki_user)
        eq_(tiki_user.userId, user.id)
