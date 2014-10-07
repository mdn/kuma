from os import listdir
from os.path import join, dirname
import re

from django.contrib.auth.models import User

import test_utils
from nose.tools import eq_

import sumo
from sumo.urlresolvers import reverse


get = lambda c, v, **kw: c.get(reverse(v, **kw), follow=True)
post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


def attrs_eq(received, **expected):
    """Compares received's attributes with expected's kwargs."""
    for k, v in expected.iteritems():
        eq_(v, getattr(received, k))


class FixtureMissingError(Exception):
    """Raise this if a fixture is missing"""


def get_user(username='testuser'):
    """Return a django user or raise FixtureMissingError"""
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        raise FixtureMissingError(
            'Username "%s" not found. You probably forgot to import a'
            ' users fixture.' % username)


class MigrationTests(test_utils.TestCase):
    """Sanity checks for the SQL migration scripts"""

    @staticmethod
    def _migrations_path():
        """Return the absolute path to the migration script folder."""
        return join(dirname(dirname(dirname(sumo.__file__))), 'migrations')

    def test_unique(self):
        """Assert that the numeric prefixes of the DB migrations are unique."""
        leading_digits = re.compile(r'^\d+')
        seen_numbers = set()
        path = self._migrations_path()
        for filename in listdir(path):
            match = leading_digits.match(filename)
            if match:
                number = match.group()
                if number in seen_numbers:
                    self.fail('There is more than one migration #%s in %s.' %
                              (number, path))
                seen_numbers.add(number)

    def test_innodb_and_utf8(self):
        """Make sure each created table uses the InnoDB engine and UTF-8."""
        # Heuristic: make sure there are at least as many "ENGINE=InnoDB"s as
        # "CREATE TABLE"s. (There might be additional "InnoDB"s in ALTER TABLE
        # statements, which are fine.)
        path = self._migrations_path()
        # The ones before 66 have known failures.
        for filename in sorted(listdir(path))[66:]:
            with open(join(path, filename)) as f:
                contents = f.read()
            creates = contents.count('CREATE TABLE')
            engines = contents.count('ENGINE=InnoDB')
            encodings = (contents.count('CHARSET=utf8') +
                         contents.count('CHARACTER SET utf8'))
            assert engines >= creates, ("There weren't as many "
                'occurrences of "ENGINE=InnoDB" as of "CREATE TABLE" in '
                'migration %s.' % filename)
            assert encodings >= creates, ("There weren't as many "
                'UTF-8 declarations as "CREATE TABLE" occurrences in '
                'migration %s.' % filename)
