#!/usr/bin/env python
"""
Usage: update_site.py [options]
Updates a server's sources, vendor libraries, packages CSS/JS
assets, migrates the database, and other nifty deployment tasks.

Options:
  -h, --help            show this help message and exit
  -e ENVIRONMENT,
  --environment=ENVIRONMENT
                        Type of environment. One of
                        (dev|stage|prod|mdn_dev|mdn_stage|mdn_prod)
                        Example:
                        update_site.py -e stage
  -v, --verbose         Echo actions before taking them.
"""

import os
import sys
from textwrap import dedent
from optparse import  OptionParser

# Constants
PROJECT = 0

ENV_BRANCH = {
    # 'env': 'git branch'
    # kuma-stage is set to 'stage'
    'dev':          'master',
    'stage':        'master',
    'mdn_dev':      'master',
    # developer-stage9 is set to 'mdn_stage'
    'mdn_stage':    'next',
    'mdn_prod':     'next',
}

PIP_INSTALL_COMPILED = "pip install -q -r requirements/compiled.txt"
RM_SETTINGS_PYC = "rm -f settings*.pyc"
GIT_PULL = "git pull -q origin %(branch)s"
GIT_RESET_HARD = "git reset --hard HEAD"
GIT_SUBMODULE_SYNC = "git submodule sync"
GIT_SUBMODULE_UPDATE = "git submodule update --init -q"
SVN_REVERT = "svn revert -R ."
SVN_UP = "svn update"
COMPILE_PO = "./compile-mo.sh ."

EXEC = 'exec'
CHDIR = 'chdir'


def update_site(env, debug):
    """Run through commands to update this site."""
    error_updating = False
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    project_branch = {'branch': ENV_BRANCH[env]}

    commands = [
        (CHDIR, here),
        (EXEC, RM_SETTINGS_PYC),
        (EXEC, GIT_RESET_HARD),
        (EXEC, GIT_PULL % project_branch),
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
        (CHDIR, os.path.join(here, 'vendor')),
        # This seems like a bad idea - it pulls from master, while the web app
        # itself has a submodule pointing at a specific vendor-lib commit ID
        (EXEC,  GIT_RESET_HARD),
        (EXEC,  GIT_SUBMODULE_SYNC),
        (EXEC,  GIT_SUBMODULE_UPDATE),
        (CHDIR, os.path.join(here)),
        (EXEC, 'python2.6 vendor/src/schematic/schematic migrations/'),
        (EXEC, 'python2.6 manage.py migrate'),
        (EXEC, 'python2.6 manage.py collectstatic --noinput'),
        (EXEC, 'LANG=en_US.UTF-8 python2.6 manage.py compress_assets'),
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
    e_help = "Type of environment. One of (%s) Example: update_site.py \
        -e stage" % '|'.join(ENV_BRANCH.keys())
    options.add_option("-e", "--environment", help=e_help)
    options.add_option("-v", "--verbose",
                       help="Echo actions before taking them.",
                       action="store_true", dest="verbose")
    (opts, _) = options.parse_args()

    if opts.verbose:
        debug = True
    if opts.environment in ENV_BRANCH.keys():
        update_site(opts.environment, debug)
    else:
        sys.stderr.write("Invalid environment!\n")
        options.print_help(sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
