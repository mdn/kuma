from __future__ import unicode_literals

import pytest
from django.core.management import call_command, CommandError
from django.utils.six import StringIO


def test_help():
    with pytest.raises(CommandError) as excinfo:
        call_command('ihavepower', stdout=StringIO())

    # if PY2:
    #     assert str(excinfo.value) == 'Error: too few arguments'
    # else:
    #     assert str(excinfo.value) == 'Error: the following arguments are required: username'
    assert str(excinfo.value) == 'Error: the following arguments are required: username'


def test_user_doesnt_exist(db):
    with pytest.raises(CommandError) as excinfo:
        call_command('ihavepower', 'fordprefect', stdout=StringIO())

    assert str(excinfo.value) == 'User fordprefect does not exist.'


def test_user_exists(wiki_user):
    assert wiki_user.is_staff is False
    assert wiki_user.is_superuser is False
    call_command('ihavepower', wiki_user.username, stdout=StringIO())
    wiki_user.refresh_from_db()
    assert wiki_user.is_staff is True
    assert wiki_user.is_superuser is True
