#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import codecs

try:
    any([True])
    any = any
except NameError:
    def any(iterable):
        for item in iterable:
            if item:
                return True
        return False

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import sys

import billiard

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
src_dir = "billiard"


def osx_install_data(install_data):

    def finalize_options(self):
        self.set_undefined_options("install", ("install_lib", "install_dir"))
        install_data.finalize_options(self)


def fullsplit(path, result=None):
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

SKIP_EXTENSIONS = [".pyc", ".pyo", ".swp", ".swo"]


def is_unwanted_file(filename):
    return any([filename.endswith(skip_ext) for skip_ext in SKIP_EXTENSIONS])


for dirpath, dirnames, filenames in os.walk(src_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."):
            del dirnames[i]
    for filename in filenames:
        if filename.endswith(".py"):
            packages.append('.'.join(fullsplit(dirpath)))
        elif is_unwanted_file(filename):
            pass
        else:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in
                filenames]])

setup(
    name='billiard',
    version=billiard.__version__,
    description=billiard.__doc__,
    author=billiard.__author__,
    author_email=billiard.__contact__,
    url=billiard.__homepage__,
    platforms=["any"],
    packages=packages,
    data_files=data_files,
    license="BSD",
    zip_safe=False,
    test_suite="nose.collector",
    install_requires=[
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
    ],
    long_description=codecs.open('README', "r", "utf-8").read(),
)
