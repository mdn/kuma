# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""Helper functions to support command line tools providing more than
one command.

e.g called as "tool command [options] args..." where <options> and <args> are
command'specific




"""
__docformat__ = "restructuredtext en"

# XXX : merge with optparser ?
import sys
from os.path import basename

from logilab.common.configuration import Configuration


DEFAULT_COPYRIGHT = '''\
Copyright (c) 2004-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
http://www.logilab.fr/ -- mailto:contact@logilab.fr'''


DEFAULT_DOC = '''\
Type "%prog <command> --help" for more information about a specific
command. Available commands are :\n'''

class BadCommandUsage(Exception):
    """Raised when an unknown command is used or when a command is not
    correctly used.
    """


class Command(Configuration):
    """Base class for command line commands."""
    arguments = ''
    name = ''
    # hidden from help ?
    hidden = False
    # max/min args, None meaning unspecified
    min_args = None
    max_args = None
    def __init__(self, __doc__=None, version=None):
        if __doc__:
            usage = __doc__ % (self.name, self.arguments,
                               self.__doc__.replace('    ', ''))
        else:
            usage = self.__doc__.replace('    ', '')
        Configuration.__init__(self, usage=usage, version=version)

    def check_args(self, args):
        """check command's arguments are provided"""
        if self.min_args is not None and len(args) < self.min_args:
            raise BadCommandUsage('missing argument')
        if self.max_args is not None and len(args) > self.max_args:
            raise BadCommandUsage('too many arguments')

    def run(self, args):
        """run the command with its specific arguments"""
        raise NotImplementedError()


def pop_arg(args_list, expected_size_after=0, msg="Missing argument"):
    """helper function to get and check command line arguments"""
    try:
        value = args_list.pop(0)
    except IndexError:
        raise BadCommandUsage(msg)
    if expected_size_after is not None and len(args_list) > expected_size_after:
        raise BadCommandUsage('too many arguments')
    return value


_COMMANDS = {}

def register_commands(commands):
    """register existing commands"""
    for command_klass in commands:
        _COMMANDS[command_klass.name] = command_klass


def main_usage(status=0, doc=DEFAULT_DOC, copyright=DEFAULT_COPYRIGHT):
    """display usage for the main program (i.e. when no command supplied)
    and exit
    """
    commands = _COMMANDS.keys()
    commands.sort()
    if doc != DEFAULT_DOC:
        try:
            doc = doc % ('<command>', '<command arguments>',
                             '''\
Type "%prog <command> --help" for more information about a specific
command. Available commands are :\n''')
        except TypeError:
            print 'could not find the "command", "arguments" and "default" slots'
    doc = doc.replace('%prog', basename(sys.argv[0]))
    print 'usage:', doc
    max_len = max([len(cmd) for cmd in commands]) # list comprehension for py 2.3 support
    padding = ' '*max_len
    for command in commands:
        cmd = _COMMANDS[command]
        if not cmd.hidden:
            title = cmd.__doc__.split('.')[0]
            print ' ', (command+padding)[:max_len], title
    if copyright:
        print '\n', copyright
    sys.exit(status)


def cmd_run(cmdname, *args):
    try:
        command = _COMMANDS[cmdname](__doc__='%%prog %s %s\n\n%s')
    except KeyError:
        raise BadCommandUsage('no %s command' % cmdname)
    args = command.load_command_line_configuration(args)
    command.check_args(args)
    try:
        command.run(args)
    except KeyboardInterrupt:
        print 'interrupted'
    except BadCommandUsage, err:
        print 'ERROR: ', err
        print command.help()


def main_run(args, doc=DEFAULT_DOC, copyright=DEFAULT_COPYRIGHT):
    """command line tool"""
    try:
        arg = args.pop(0)
    except IndexError:
        main_usage(status=1, doc=doc, copyright=copyright)
    if arg in ('-h', '--help'):
        main_usage(doc=doc, copyright=copyright)
    try:
        cmd_run(arg, *args)
    except BadCommandUsage, err:
        print 'ERROR: ', err
        main_usage(1, doc=doc, copyright=copyright)


class ListCommandsCommand(Command):
    """list available commands, useful for bash completion."""
    name = 'listcommands'
    arguments = '[command]'
    hidden = True

    def run(self, args):
        """run the command with its specific arguments"""
        if args:
            command = pop_arg(args)
            cmd = _COMMANDS[command]
            for optname, optdict in cmd.options:
                print '--help'
                print '--' + optname
        else:
            commands = _COMMANDS.keys()
            commands.sort()
            for command in commands:
                cmd = _COMMANDS[command]
                if not cmd.hidden:
                    print command

register_commands([ListCommandsCommand])
