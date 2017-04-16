#! /usr/bin/python

# Copyright (C) 2007-2009 Michael Foord
# E-mail: fuzzyman AT voidspace DOT org DOT uk
# http://www.voidspace.org.uk/python/mock/

from textwrap import dedent
from mock import __version__

from distutils.core import setup

setup(
    name = "mock",
    version = __version__,
    py_modules = ['mock'],
    
    # metadata for upload to PyPI
    author = "Michael Foord",
    author_email = "fuzzyman@voidspace.org.uk",
    description = "A Python mock object library",
    long_description = dedent("""\
    Mock is a flexible mock object intended to replace the use of stubs and test doubles 
    throughout your code. Mocks are callable and create attributes as new mocks when you 
    access them. Accessing the same attribute will always return the same mock. Mocks 
    record how you use them, allowing you to make assertions about what your code has 
    done to them."""),
    license = "BSD",
    keywords = "testing test mock mocking unittest patching stubs",
    url = "http://www.voidspace.org.uk/python/mock/",
    download_url = 'http://www.voidspace.org.uk/downloads/mock-%s.zip' % __version__,

)
