#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

from distutils.cmd import Command
import doctest
from glob import glob
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys

sys.path.append(os.path.join('doc', 'common'))
try:
    from doctools import build_doc, test_doc
except ImportError:
    build_doc = test_doc = None


setup(
    name = 'Babel',
    version = '0.9.5',
    description = 'Internationalization utilities',
    long_description = \
"""A collection of tools for internationalizing Python applications.""",
    author = 'Edgewall Software',
    author_email = 'info@edgewall.org',
    license = 'BSD',
    url = 'http://babel.edgewall.org/',
    download_url = 'http://babel.edgewall.org/wiki/Download',
    zip_safe = False,

    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages = ['babel', 'babel.messages'],
    package_data = {'babel': ['global.dat', 'localedata/*.dat']},
    test_suite = 'babel.tests.suite',
    tests_require = ['pytz'],

    entry_points = """
    [console_scripts]
    pybabel = babel.messages.frontend:main
    
    [distutils.commands]
    compile_catalog = babel.messages.frontend:compile_catalog
    extract_messages = babel.messages.frontend:extract_messages
    init_catalog = babel.messages.frontend:init_catalog
    update_catalog = babel.messages.frontend:update_catalog
    
    [distutils.setup_keywords]
    message_extractors = babel.messages.frontend:check_message_extractors
    
    [babel.checkers]
    num_plurals = babel.messages.checkers:num_plurals
    python_format = babel.messages.checkers:python_format
    
    [babel.extractors]
    ignore = babel.messages.extract:extract_nothing
    python = babel.messages.extract:extract_python
    javascript = babel.messages.extract:extract_javascript
    """,

    cmdclass = {'build_doc': build_doc, 'test_doc': test_doc}
)
