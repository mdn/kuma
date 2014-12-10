#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import codecs
import platform

try:
    from setuptools import setup, find_packages, Command
    from setuptools.command.test import test as TestCommand
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages, Command
    from setuptools.command.test import test as TestCommand

import pyes as distmeta


class QuickRunTests(TestCommand):
    extra_env = dict(SKIP_RLIMITS=1, QUICKTEST=1)

    def run(self, *args, **kwargs):
        for env_name, env_value in self.extra_env.items():
            os.environ[env_name] = str(env_value)
        TestCommand.run(self, *args, **kwargs)


install_requires = []

#if not sys.platform.startswith("java"):
#    install_requires += [ "thrift", ]    
try:
    import importlib
except ImportError:
    install_requires.append("importlib")

try:
    # For Python >= 2.6
    import json
except ImportError:
    # For Python < 2.6 or people using a newer version of simplejson
    install_requires.append("simplejson")

py_version = sys.version_info
if not sys.platform.startswith("java") and sys.version_info < (2, 6):
    install_requires.append("multiprocessing==2.6.2.1")

if os.path.exists("README.rst"):
    long_description = codecs.open("README.rst", "r", "utf-8").read()
else:
    long_description = "See http://pypi.python.org/pypi/pyes"

setup(
    name='pyes',
    version=distmeta.__version__,
    description="Python Elastic Search driver",
    author=distmeta.__author__,
    author_email=distmeta.__contact__,
    url=distmeta.__homepage__,
    platforms=["any"],
    license="BSD",
    packages=find_packages(exclude=['ez_setup', 'tests', 'tests.*', "docs.*"]),
    scripts=[],
    zip_safe=False,
    install_requires=install_requires,
    tests_require=['nose', 'nose-cover3', 'unittest2', 'simplejson'],
    cmdclass={"quicktest": QuickRunTests},
    test_suite="nose.collector",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search'
    ],
    entry_points={
        'console_scripts': [],
    },
    long_description=long_description,
)
