# -*- coding: utf-8 -*-
# file2.py for tests

from gettext import ngettext

def foo():
    # Note: This will have the TRANSLATOR: tag but shouldn't
    # be included on the extracted stuff
    print ngettext('foobar', 'foobars', 1)
