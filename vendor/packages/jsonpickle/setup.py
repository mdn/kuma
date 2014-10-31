#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Paulett (john -at- paulett.org)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


import sys
import jsonpickle as _jsonpickle

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


INSTALL_REQUIRES = []
if sys.version_info[:2] <= (2, 5):
    INSTALL_REQUIRES.append('simplejson')


SETUP_ARGS = dict(
    name="jsonpickle",
    version=_jsonpickle.__version__,
    description="Python library for serializing any "
                "arbitrary object graph into JSON",
    long_description = _jsonpickle.__doc__,
    author="John Paulett",
    author_email="john -at- paulett.org",
    url="http://jsonpickle.github.com/",
    license="BSD",
    platforms=['POSIX', 'Windows'],
    keywords=['json pickle', 'json', 'pickle', 'marshal',
              'serialization', 'JavaScript Object Notation'],
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript"
    ],
    options={'clean': {'all': 1}},
    packages=["jsonpickle"],
    test_suite='jsonpickle.tests.suite',
    install_requires=INSTALL_REQUIRES,
    zip_safe=True,
)


def main():
    setup(**SETUP_ARGS)
    return 0


if __name__ == '__main__':
    sys.exit(main())
