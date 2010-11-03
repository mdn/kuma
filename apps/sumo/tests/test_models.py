from os import listdir
from os.path import join, dirname
import re

import jingo
from nose.tools import eq_

import sumo
from sumo import backends
from sumo.models import WikiPage, TikiUser
from sumo.tests import TestCase


def setup():
    jingo.load_helpers()


class TestWikiPage(TestCase):
    fixtures = ['pages.json']

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


class MigrationNumberTests(TestCase):
    def test_unique(self):
        """Assert that the numeric prefixes of the DB migrations are unique."""
        leading_digits = re.compile(r'^\d+')
        path = join(dirname(dirname(dirname(sumo.__file__))), 'migrations')
        seen_numbers = set()
        for node in listdir(path):
            match = leading_digits.match(node)
            if match:
                number = match.group()
                if number in seen_numbers:
                    self.fail('There is more than one migration #%s in %s.' %
                              (number, path))
                seen_numbers.add(number)
