#!/usr/bin/env python
"""
Run all the unittest modules for amqplib.client_0_8

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

import sys
import unittest

import settings

TEST_NAMES = [
        'test_exceptions',
        'test_serialization',
        'test_basic_message',
        'test_connection',
        'test_channel',
        ]

if sys.version_info >= (2, 5):
    TEST_NAMES.append('test_with')

def main():
    suite = unittest.TestLoader().loadTestsFromNames(TEST_NAMES)
    unittest.TextTestRunner(**settings.test_args).run(suite)

if __name__ == '__main__':
    main()
