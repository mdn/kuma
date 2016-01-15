from django.core.management import call_command, CommandError
from django.utils.six import StringIO

from kuma.users.tests import user, UserTestCase


class TestIHavePowerCommand(UserTestCase):
    def test_help(self):
        out = StringIO()
        with self.assertRaises(CommandError) as commanderror_cm:
            call_command('ihavepower', stdout=out)

        commanderror = commanderror_cm.exception
        assert commanderror.message == 'Error: too few arguments'

    def test_user_doesnt_exist(self):
        out = StringIO()
        with self.assertRaises(CommandError) as commanderror_cm:
            call_command('ihavepower', 'fordprefect', stdout=out)

        commanderror = commanderror_cm.exception
        assert commanderror.message == 'User fordprefect does not exist.'

    def test_user_exists(self):
        out = StringIO()
        user(username='fordprefect', save=True)
        call_command('ihavepower', 'fordprefect', stdout=out)

        ford = self.user_model.objects.get(username='fordprefect')
        assert ford.is_staff is True
        assert ford.is_superuser is True
