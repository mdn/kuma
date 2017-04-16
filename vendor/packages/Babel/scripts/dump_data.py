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

from optparse import OptionParser
from pprint import pprint
import sys

from babel.localedata import load, LocaleDataDict


def main():
    parser = OptionParser(usage='%prog [options] locale [path]')
    parser.add_option('--noinherit', action='store_false', dest='inherit',
                      help='do not merge inherited data into locale data')
    parser.add_option('--resolve', action='store_true', dest='resolve',
                      help='resolve aliases in locale data')
    parser.set_defaults(inherit=True, resolve=False)
    options, args = parser.parse_args()
    if len(args) not in (1, 2):
        parser.error('incorrect number of arguments')

    data = load(args[0], merge_inherited=options.inherit)
    if options.resolve:
        data = LocaleDataDict(data)
    if len(args) > 1:
        for key in args[1].split('.'):
            data = data[key]
    if isinstance(data, dict):
        data = dict(data.items())
    pprint(data)


if __name__ == '__main__':
    main()
