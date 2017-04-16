 # -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2006 ThoughtWorks, Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
##############################################################################

from ez_setup import use_setuptools
use_setuptools()

import os
import sys
import string

from setuptools import setup, find_packages
here = os.path.abspath(os.path.normpath(os.path.dirname(__file__)))

DESC = """Selenium Python Client Driver is a Python language binding for \
Selenium Remote Control"""

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Quality Assurance',
    'Topic :: Software Development :: Testing',
    ]

selenium_version = "1.0.1"

dist = setup(
    name = 'selenium',
    version = selenium_version,
    license = 'Apache 2.0 (http://www.apache.org/licenses/LICENSE-2.0)',
    url = 'http://www.openqa.org/',
    download_url = 'http://www.openqa.org/',
    description = "A Python language binding for Selenium RC",
    long_description= DESC,
    classifiers = CLASSIFIERS,
    author = "Dan Fabulich",
    author_email = "dfabulich@warpmail.net",
    maintainer = "Maik Roeder",
    maintainer_email = "roeder@berg.net",
    package_dir = {'':'src'},
    py_modules=['selenium'],
    # put data files in egg 'doc' dir
    data_files=[ ('doc', [
        'README.txt',
        ]
    )],
    include_package_data = True,
    zip_safe = False,
    )
