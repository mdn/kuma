from os import listdir
from os.path import join, dirname
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import Client

from test_utils import TestCase  # So others can import it from here

import sumo
from sumo.urlresolvers import reverse, split_path


get = lambda c, v, **kw: c.get(reverse(v, **kw), follow=True)
post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


class LocalizingClient(Client):
    """Client which prepends a locale so test requests can get through
    LocaleURLMiddleware without resulting in a locale-prefix-adding 301.

    Otherwise, we'd have to hard-code locales into our tests everywhere or
    {mock out reverse() and make LocaleURLMiddleware not fire}.

    """
    def request(self, **request):
        """Make a request, but prepend a locale if there isn't one already."""
        # Fall back to defaults as in the superclass's implementation:
        path = request.get('PATH_INFO', self.defaults.get('PATH_INFO', '/'))
        locale, shortened = split_path(path)
        if not locale:
            request['PATH_INFO'] = '/%s/%s' % (settings.LANGUAGE_CODE,
                                               shortened)
        return super(LocalizingClient, self).request(**request)

    # If you use this, you might also find the force_locale=True argument to
    # sumo.urlresolvers.reverse() handy, in case you need to force locale
    # prepending in a one-off case or do it outside a mock request.


class FixtureMissingError(Exception):
    """Raise this if a fixture is missing"""


def get_user(username='jsocol'):
    """Return a django user or raise FixtureMissingError"""
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        raise FixtureMissingError(
            'Username "%s" not found. You probably forgot to import a'
            ' users fixture.' % username)


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

