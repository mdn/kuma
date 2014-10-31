#!/usr/bin/env python
"""
Test the amqplib.client_0_8.basic_message module.

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

from datetime import datetime
from decimal import Decimal
import unittest

import settings

from amqplib.client_0_8.basic_message import Message


class TestBasicMessage(unittest.TestCase):

    def check_proplist(self, msg):
        """
        Check roundtrip processing of a single object

        """
        raw_properties = msg._serialize_properties()

        new_msg = Message()
        new_msg._load_properties(raw_properties)
        new_msg.body = msg.body

        self.assertEqual(msg, new_msg)


    def test_roundtrip(self):
        """
        Check round-trip processing of content-properties.

        """
        self.check_proplist(Message())

        self.check_proplist(Message(content_type='text/plain'))

        self.check_proplist(Message(
            content_type='text/plain',
            content_encoding='utf-8',
            application_headers={'foo': 7, 'bar': 'baz', 'd2': {'foo2': 'xxx', 'foo3': -1}},
            delivery_mode=1,
            priority=7))

        self.check_proplist(Message(
            application_headers={
                'regular': datetime(2007, 11, 12, 12, 34, 56),
                'dst': datetime(2007, 7, 12, 12, 34, 56),
                }))

        n = datetime.now()
        n = n.replace(microsecond=0) # AMQP only does timestamps to 1-second resolution
        self.check_proplist(Message(
            application_headers={'foo': n}))

        self.check_proplist(Message(
            application_headers={'foo': Decimal('10.1')}))

        self.check_proplist(Message(
            application_headers={'foo': Decimal('-1987654.193')}))

        self.check_proplist(Message(timestamp=datetime(1980, 1, 2, 3, 4, 6)))


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBasicMessage)
    unittest.TextTestRunner(**settings.test_args).run(suite)


if __name__ == '__main__':
    main()
