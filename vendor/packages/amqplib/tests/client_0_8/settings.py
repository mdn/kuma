"""
Parse commandline args for running unittests.  Used
by the overall run_all.py script, or the various
indivudial test modules that need settings for connecting
to a broker.

"""
# Copyright (C) 2007-2008 Barry Pederson <bp@barryp.org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301

import logging
from optparse import OptionParser

connect_args = {}
test_args = {'verbosity': 1}


def parse_args():
    parser = OptionParser(usage='usage: %prog [options]')
    parser.add_option('--host', dest='host',
                        help='AMQP server to connect to (default: %default)',
                        default='localhost')
    parser.add_option('-u', '--userid', dest='userid',
                        help='userid to authenticate as (default: %default)',
                        default='guest')
    parser.add_option('-p', '--password', dest='password',
                        help='password to authenticate with (default: %default)',
                        default='guest')
    parser.add_option('--ssl', dest='ssl', action='store_true',
                        help='Enable SSL (default: not enabled)',
                        default=False)
    parser.add_option('--debug', dest='debug', action='store_true',
                        help='Display debugging output',
                        default=False)

    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                        help='Run unittests with increased verbosity',
                        default=False)

    options, args = parser.parse_args()

    if options.debug:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        amqplib_logger = logging.getLogger('amqplib')
        amqplib_logger.addHandler(console)
        amqplib_logger.setLevel(logging.DEBUG)

    connect_args['host'] = options.host
    connect_args['userid'] = options.userid
    connect_args['password'] = options.password
    connect_args['ssl'] = options.ssl

    if options.verbose:
        test_args['verbosity'] = 2

parse_args()
