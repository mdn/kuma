#!/usr/bin/env python
"""
Usage: update_site.py [options]

Updates the developer-dev.allizom.org server

Options:
  -h, --help            show this help message and exit
  -v, --verbose         Echo actions before taking them.
"""

import os
import sys
from textwrap import dedent
from optparse import OptionParser

RM_SETTINGS_PYC = "rm -f settings*.pyc"
GIT_PULL = "git pull -q origin master"
GIT_RESET_HARD = "git reset --hard HEAD"
GIT_SUBMODULE_SYNC = "git submodule sync"
GIT_SUBMODULE_UPDATE = "git submodule update --init -q"
GIT_REVISION_TXT = "git rev-parse HEAD > media/revision.txt"
SVN_REVERT = "svn revert -R ."
SVN_UP = "svn update"
COMPILE_PO = "./compile-mo.sh ."

EXEC = 'exec'
CHDIR = 'chdir'


def update_site(debug):
    """Run through commands to update this site."""
    error_updating = False
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    commands = [
        (CHDIR, here),
        (EXEC, RM_SETTINGS_PYC),
        (EXEC, GIT_RESET_HARD),
        (EXEC, GIT_PULL),
        (EXEC, GIT_SUBMODULE_SYNC),
        (EXEC, GIT_SUBMODULE_UPDATE),
    ]

    # Update locale dir if applicable
    if os.path.exists(os.path.join(here, 'locale', '.svn')):
        commands += [
            (CHDIR, os.path.join(here, 'locale')),
            (EXEC, SVN_REVERT),
            (EXEC, SVN_UP),
            (EXEC, COMPILE_PO),
            (CHDIR, here),
        ]
    elif os.path.exists(os.path.join(here, 'locale', '.git')):
        commands += [
            (CHDIR, os.path.join(here, 'locale')),
            (EXEC, GIT_PULL % 'master'),
            (CHDIR, here),
        ]

    commands += [
        (EXEC, 'python2.6 manage.py syncdb --noinput'),

        (EXEC, 'python2.6 manage.py migrate --noinput'),
        (EXEC, 'python2.6 manage.py update_badges'),
        (EXEC, 'python2.6 manage.py collectstatic --noinput'),
        (EXEC, GIT_REVISION_TXT),
    ]

    for cmd, cmd_args in commands:
        if CHDIR == cmd:
            if debug:
                sys.stdout.write("cd %s\n" % cmd_args)
            os.chdir(cmd_args)
        elif EXEC == cmd:
            if debug:
                sys.stdout.write("%s\n" % cmd_args)
            if not 0 == os.system(cmd_args):
                error_updating = True
                break
        else:
            raise Exception("Unknown type of command %s" % cmd)

    if error_updating:
        sys.stderr.write("There was an error while updating. Please try again "
                         "later. Aborting.\n")


def main():
    """ Handels command line args. """
    debug = False
    usage = dedent("""\
        %prog [options]
        Updates a server's sources, vendor libraries, packages CSS/JS
        assets, migrates the database, and other nifty deployment tasks.
        """.rstrip())

    options = OptionParser(usage=usage)
    options.add_option("-v", "--verbose",
                       help="Echo actions before taking them.",
                       action="store_true", dest="verbose")
    (opts, _) = options.parse_args()

    if opts.verbose:
        debug = True
    update_site(debug)


if __name__ == '__main__':
    main()
