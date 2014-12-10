#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Paulett (john -at- paulett.org)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest

import util_tests
import jsonpickle_test
import thirdparty_tests

def suite():
    suite = unittest.TestSuite()
    suite.addTest(util_tests.suite())
    suite.addTest(jsonpickle_test.suite())
    suite.addTest(thirdparty_tests.suite())
    return suite

def main():
    #unittest.main(defaultTest='suite')
    unittest.TextTestRunner(verbosity=2).run(suite())

if __name__ == '__main__':
    main()
