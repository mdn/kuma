from django.core.management import call_command, CommandError
from django.utils.six import StringIO

from nose.tools import eq_

from kuma.core.tests import TestCase
from kuma.users.models import User
from kuma.users.tests import user


class TestIHavePowerCommand(TestCase):
    def test_help(self):
        out = StringIO()
        with self.assertRaises(CommandError) as cm:
            call_command('ihavepower', stdout=out)

        exc = cm.exception
        eq_(exc.message, 'Error: too few arguments')

    def test_user_doesnt_exist(self):
        out = StringIO()
        with self.assertRaises(CommandError) as cm:
            call_command('ihavepower', 'fordprefect', stdout=out)

        exc = cm.exception
        eq_(exc.message, 'User fordprefect does not exist.')

    def test_user_exists(self):
        out = StringIO()
        user(username='fordprefect', save=True)
        call_command('ihavepower', 'fordprefect', stdout=out)

        ford = User.objects.get(username='fordprefect')
        eq_(ford.is_staff, True)
        eq_(ford.is_superuser, True)
