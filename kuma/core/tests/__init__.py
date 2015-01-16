from django.contrib.auth.models import User

from nose.tools import eq_

from ..urlresolvers import reverse


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
