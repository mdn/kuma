#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Paulett (john -at- paulett.org)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import sys
import timeit

IS_25_DOWN = sys.version_info[:2] <= (2, 5)

number = 1000

mod = 'json'
if IS_25_DOWN:
    mod = 'simplejson'

json = """\
import feedparser
import jsonpickle
import jsonpickle.tests.thirdparty_tests as test
doc = feedparser.parse(test.RSS_DOC)

jsonpickle.set_preferred_backend('%s')

pickled = jsonpickle.encode(doc)
unpickled = jsonpickle.decode(pickled)
if doc['feed']['title'] != unpickled['feed']['title']:
    print 'Not a match'
""" % mod

print 'Using %s' % mod
json_test = timeit.Timer(stmt=json)
print "%.9f sec/pass " % (json_test.timeit(number=number) / number)
