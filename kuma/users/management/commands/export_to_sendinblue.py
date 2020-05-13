# The implementation lives over there, this file has to exist because of
# Django's conventions around management commands. I.e. the name of
# this file determines how the command is called.
from kuma.users.sendinblue.commands import ExportCommand as Command  # noqa
