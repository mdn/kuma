# -*- coding: utf-8 -*-
""" Platform specific utility functions, posix version 

Importing this module directly is not portable - rather, import platutils 
to use these functions in platform agnostic fashion.
"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import sys
import os

ignore_termtitle = True

def _dummy_op(*a, **b):
    """ A no-op function """


def _set_term_title_xterm(title):
    """ Change virtual terminal title in xterm-workalikes """

    sys.stdout.write('\033]0;%s\007' % title)


if os.environ.get('TERM','') == 'xterm':
    set_term_title = _set_term_title_xterm
else:
    set_term_title = _dummy_op


def find_cmd(cmd):
    """Find the full path to a command using which."""
    return os.popen('which %s' % cmd).read().strip()


def get_long_path_name(path):
    """Dummy no-op."""
    return path


def term_clear():
    os.system('clear')
