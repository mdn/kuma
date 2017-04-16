# -*- coding: utf-8 -*-

# This file won't normally be in this directory.
# It IS only for tests

from gettext import ngettext

def foo():
    # Note: This will have the TRANSLATOR: tag but shouldn't
    # be included on the extracted stuff
    print ngettext('FooBar', 'FooBars', 1)
