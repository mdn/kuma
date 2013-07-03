#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import site
import sys
import logging
from os.path import dirname, abspath

from django.conf import settings


logging.basicConfig()

if not settings.configured:
    settings.configure(
        DATABASE_ENGINE='sqlite3',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'taggit',
            #'taggit.tests',
            'taggit_extras.tests',
        ]
    )

from django.test.simple import run_tests


def runtests(*test_args):

    if not test_args:
        test_args = ['tests']
    
    ROOT = os.path.join(
        dirname(os.path.abspath(__file__)),
        '..', '..', '..'
    )
    path = lambda *a: os.path.join(ROOT, *a)

    prev_sys_path = list(sys.path)

    site.addsitedir(path('apps'))
    site.addsitedir(path('lib'))
    site.addsitedir(path('vendor'))

    # Move the new items to the front of sys.path.
    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path

    parent = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..",
    )
    sys.path.insert(0, parent)

    failures = run_tests(test_args, verbosity=1, interactive=True)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])
